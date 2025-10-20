from os import getenv
from bot.utils.shop_logic import get_shop_config, check_order_cooldown, check_item_rules, PHASE_NAMES, STATUS_EMOJI
from datetime import timezone
import datetime
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from bson.objectid import ObjectId

from bot.utils.td_dg import (
    products_collection, teams_collection, orders_collection, is_team_exist, is_team_password_correct
)
from bot.utils.sheetslogger import log_action 

class CaptainActions(StatesGroup):
    shop_choosing_quantity = State()
    writing_exchange_request = State()
    writing_return_request = State()

router = Router()

async def view_shop_page(message_or_callback, state: FSMContext, page: int):
    if isinstance(message_or_callback, types.CallbackQuery):
        message = message_or_callback.message
    else:
        message = message_or_callback

    config = await get_shop_config()
    current_phase = config['phase']
    
    ITEMS_PER_PAGE = 5
    skip = (page - 1) * ITEMS_PER_PAGE

    db_filter = {"stock_quantity": {"$gt": 0}}
    
    if current_phase == 1:
        db_filter["description"] = {"$in": ["Tier 1", "Tier 2", "Tier 3"]}
    elif current_phase == 2:
        db_filter["description"] = {"$in": ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5", "Tier 6"]}

    products = await products_collection.find(db_filter).skip(skip).limit(ITEMS_PER_PAGE).to_list(length=ITEMS_PER_PAGE)
    total_items = await products_collection.count_documents(db_filter)
    
    user = await teams_collection.find_one({"telegram_id": str(message_or_callback.from_user.id)})
    
    timestamp = datetime.datetime.now(timezone.utc).strftime('%H:%M:%S UTC')
    text = (f"🛍️ **Магазин** (Фаза: *{PHASE_NAMES[current_phase]}*)\n")

    if not config['is_open']:
        text += "🔴 **УВАГА: Магазин наразі зачинено!**\n\n"
    elif current_phase == 0:
        text += "⚪️ **УВАГА: Магазин працює в режимі перегляду.**\n\n"

    keyboard_rows = []
    if products:
       for p in products:
           stock_info = f"(На складі: {p['stock_quantity']} шт.)"
           
           if current_phase == 2:
               allowed = p.get("allowed_to_buy")
               if allowed is not None:
                   stock_info = f"(На складі: {p['stock_quantity']} шт. | Можна купити: {allowed} шт.)"
           text += (f"🔹 **{p['name']}**\n"
                    f"   Ціна: {p['price_coupons']} купонів {stock_info}\n\n")
                    
           if config['is_open'] and current_phase > 0:
               keyboard_rows.append([InlineKeyboardButton(text=f"➕ Додати '{p['name']}'", callback_data=f"addtocart_{p['_id']}")])
    else:
        text += "Товарів немає."

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Попередня", callback_data=f"shoppage_{page-1}"))
    if total_items > page * ITEMS_PER_PAGE:
        nav_buttons.append(InlineKeyboardButton(text="Наступна ➡️", callback_data=f"shoppage_{page+1}"))
    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    keyboard_rows.append([InlineKeyboardButton(text="🛒 Перейти до кошика", callback_data="view_cart")])
    keyboard_rows.append([InlineKeyboardButton(text="⬅️ Назад до гол. меню", callback_data="captain_main_menu")])
    
    if isinstance(message_or_callback, types.CallbackQuery):
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows), parse_mode="Markdown")
        
# --- 1. МАГАЗИН (вхід та пагінація) ---
@router.callback_query(F.data == "captain_shop")
async def show_shop_start(callback: types.CallbackQuery, state: FSMContext):
    """Вхідна точка в магазин. Очищує старий кошик і показує 1-шу сторінку."""
    await state.update_data(cart={})
    # Видаляємо попереднє повідомлення меню, щоб уникнути плутанини
    await callback.message.delete()
    await view_shop_page(callback.message, state, page=1)

@router.callback_query(F.data.startswith("shoppage_"))
async def handle_shop_page(callback: types.CallbackQuery, state: FSMContext):
    """Обробляє натискання кнопок пагінації в магазині."""
    page = int(callback.data.split("_")[1])
    await view_shop_page(callback, state, page=page)

# --- 2. ДОДАВАННЯ ТОВАРУ В КОШИК ---
@router.callback_query(F.data.startswith("addtocart_"))
async def add_to_cart_start(callback: types.CallbackQuery, state: FSMContext):
    product_id = ObjectId(callback.data.split("_")[1])
    product = await products_collection.find_one({"_id": product_id})
    if not product:
        return await callback.answer("Товар не знайдено.", show_alert=True)
    
    await state.set_state(CaptainActions.shop_choosing_quantity)
    await state.update_data(product_to_add=str(product_id))
    await callback.message.answer(f"Введіть кількість для товару '{product['name']}' (доступно: {product['stock_quantity']}):")

@router.message(CaptainActions.shop_choosing_quantity)
async def add_to_cart_quantity(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        return await message.answer("Будь ласка, введіть додатне число.")
    
    quantity = int(message.text)
    data = await state.get_data()
    product_id = ObjectId(data.get("product_to_add"))
    
    is_allowed, reason = await check_item_rules(product_id, quantity)
    if not is_allowed:
        return await message.answer(f"❌ **Помилка:** {reason}\n\nВведіть іншу кількість або поверніться в магазин.")
        
    product = await products_collection.find_one({"_id": product_id})
    if quantity > product['stock_quantity']:
        return await message.answer(f"Недостатньо товару на складі. Максимум: {product['stock_quantity']}.")
        
    cart = data.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    
    await state.update_data(cart=cart)
    await state.set_state(None)
    await message.answer(f"✅ Додано '{product['name']}' x{quantity} до кошика.")
    await view_shop_page(message, state, page=1)


# --- 3. КОШИК ТА ОФОРМЛЕННЯ ЗАМОВЛЕННЯ ---
@router.callback_query(F.data == "view_cart" or F.data == "captain_cart")
async def view_cart(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})

    if not cart:
        return await callback.answer("🛒 Ваш кошик порожній!", show_alert=True)
    
    user = await teams_collection.find_one({"telegram_id": str(callback.from_user.id)})
    
    total_cost = 0
    cart_text = "🛒 **Ваш кошик:**\n\n"
    
    for product_id_str, quantity in cart.items():
        product = await products_collection.find_one({"_id": ObjectId(product_id_str)})
        item_total = product['price_coupons'] * quantity
        total_cost += item_total
        cart_text += f"🔹 {product['name']} - {quantity} шт. x {product['price_coupons']} = {item_total} купонів\n"

    cart_text += f"\n**Загальна сума:** {total_cost} купонів"
    cart_text += f"\n**Ваш баланс:** {user['budget']} купонів"

    keyboard = [[InlineKeyboardButton(text="✅ Оформити замовлення", callback_data="place_order")],
                [InlineKeyboardButton(text="🗑️ Очистити кошик", callback_data="clear_cart")],
                [InlineKeyboardButton(text="🛍️ Продовжити покупки", callback_data="captain_shop_continue")]]
    
    await callback.message.edit_text(cart_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data == "captain_shop_continue")
async def continue_shopping(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await view_shop_page(callback.message, state, page=1)

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await callback.answer("Кошик очищено!", show_alert=True)
    await callback.message.delete()
    await view_shop_page(callback.message, state, page=1)
   
@router.callback_query(F.data == "place_order")
async def place_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.edit_text("Замовлення обробляється, будь ласка, зачекайте...")
    data = await state.get_data()
    cart = data.get("cart", {})
    user = await teams_collection.find_one({"telegram_id": str(callback.from_user.id)})
    team_name = user['team_name']
    
    # 1. Спочатку перевіряємо глобальне правило інтервалу для всього замовлення
    is_order_allowed, order_reason = await check_order_cooldown(team_name)
    if not is_order_allowed:
        return await callback.message.edit_text(f"❌ Помилка: {order_reason}")

    items_for_order, total_cost = [], 0
    for product_id_str, quantity in cart.items():
        product_id = ObjectId(product_id_str)
        
        # Перевірка правил на рівні товару
        is_item_allowed, item_reason = await check_item_rules(product_id, quantity)
        if not is_item_allowed:
            await callback.message.edit_text(f"❌ Помилка: {item_reason}\nСпробуйте сформувати кошик заново.")
            return await state.update_data(cart={})

        product = await products_collection.find_one({"_id": product_id})
        if quantity > product['stock_quantity']:
            await callback.message.edit_text(f"❌ Помилка: '{product['name']}' недостатньо на складі.")
            return await state.update_data(cart={})
            
        total_cost += product['price_coupons'] * quantity
        items_for_order.append({"product_id": product_id, "product_name": product['name'], "quantity": quantity, "price_per_item": product['price_coupons']})

    if total_cost > user['budget']:
        return await callback.message.edit_text(f"❌ Помилка: недостатньо купонів. Ваш баланс: {user['budget']}, потрібно: {total_cost}.")

    # --- ТРАНЗАКЦІЯ ---
    try:
        last_order_number = await orders_collection.count_documents({})
        
        # Створюємо змінну з часом для діагностики
        order_creation_time = datetime.datetime.now(timezone.utc)
        
        # --- ДІАГНОСТИЧНИЙ PRINT ---
        # print(f"[DEBUG] Час, що ЗАПИСУЄТЬСЯ в базу: {order_creation_time}, TZinfo: {order_creation_time.tzinfo}")

        order_doc = {
            "order_number": last_order_number + 1, "team_name": team_name,
            "captain_telegram_id": callback.from_user.id, "items": items_for_order,
            "total_cost": total_cost, "status": "new", "created_at": order_creation_time
        }
        await orders_collection.insert_one(order_doc)
        for item in items_for_order:
            await products_collection.update_one({"_id": item['product_id']}, {"$inc": {"stock_quantity": -item['quantity']}})
        
        await teams_collection.update_many({"team_name": team_name}, {"$inc": {"budget": -total_cost}})
        
        last_order_number = await orders_collection.count_documents({})
        order_doc = {
            "order_number": last_order_number + 1, "team_name": team_name,
            "captain_telegram_id": callback.from_user.id, 
            "items": items_for_order,
            "total_cost": total_cost, "status": "new", 
            "created_at": datetime.datetime.now(timezone.utc)
        }

        try:
            helpdesk_chat_id = await teams_collection.find({"role": "helpdesk"}).distinct("telegram_id")
            if helpdesk_chat_id:
                for helpdesk_id in helpdesk_chat_id:
                    helpdesk_chat_id = int(helpdesk_id)
                    notification_text = (f"🔔 **Нове замовлення!**\n\n"
                                        f"**№{order_doc['order_number']}** від команди **{team_name}**.\n"
                                        f"Зайдіть в меню 'Активні замовлення' для обробки.")
                    await bot.send_message(helpdesk_id, notification_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Помилка відправки сповіщення для HelpDesk: {e}")

        await state.update_data(cart={})
        await callback.message.edit_text(f"✅ Ваше замовлення №{order_doc['order_number']} успішно оформлено! Очікуйте на сповіщення.")
        await log_action(
            action="Order Placed",
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            team_name=team_name,
            details=f"Order #{order_doc['order_number']}, Cost: {total_cost}"
        )
    except Exception as e:
        await callback.message.edit_text("❌ Сталася критична помилка. Зверніться до організаторів.")
        await log_action("CRITICAL Order Error", callback.from_user.id, str(e))
