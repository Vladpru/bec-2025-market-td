
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from bson.objectid import ObjectId

# Важливо: імпортуйте всі потрібні колекції та функції
from bot.utils.shop_logic import STATUS_EMOJI
from bot.utils.td_dg import (
    products_collection, users_collection, orders_collection, is_team_exist, is_team_password_correct
)
from bot.utils.sheetslogger import log_action 
from bot.keyboards.choices import captain_menu_kb

router = Router()

class CaptainLogin(StatesGroup):
    team_name = State()
    password = State()

# --- АВТОРИЗАЦІЯ ---
@router.message(F.text == "Командир команди")
async def captain_login_start(message: types.Message, state: FSMContext):
    await state.set_state(CaptainLogin.team_name)
    await message.answer("Введіть назву команди:", reply_markup=ReplyKeyboardRemove())

@router.message(CaptainLogin.team_name)
async def process_team_name(message: types.Message, state: FSMContext):
    team_name = message.text
    if await is_team_exist(team_name):
        await state.update_data(team_name=team_name)
        await state.set_state(CaptainLogin.password)
        await message.answer("Введіть пароль команди:")
    else:
        await message.answer("Такої команди не існує. Спробуйте знову.")

@router.message(CaptainLogin.password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    user_data = await state.get_data()
    team_name = user_data.get("team_name")

    # 1. Шукаємо повний документ команди за назвою та паролем
    team_doc = await users_collection.find_one({"team_name": team_name, "team_password": password})

    if team_doc:
        # 2. Якщо знайдено, оновлюємо САМЕ ЦЕЙ ДОКУМЕНТ, додаючи/оновлюючи telegram_id
        await users_collection.update_one(
            {"_id": team_doc["_id"]}, # Оновлюємо по унікальному ID знайденого документа
            {"$set": {
                "telegram_id": str(message.from_user.id),
                "username": message.from_user.username,
                "role": "captain"
            }}
        )
        
        await state.clear()
        await message.answer(f"Вітаємо, командире {team_name}! Оберіть одну з дій:", reply_markup=captain_menu_kb)
    else:
        await message.answer("Помилка авторизації. Спробуйте знову.")

# --- ГОЛОВНЕ МЕНЮ ---
@router.callback_query(F.data == "captain_main_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Оберіть одну з дій:", reply_markup=captain_menu_kb)

# --- БАЛАНС ---
@router.callback_query(F.data == "captain_coupons")
async def show_coupons(callback: types.CallbackQuery):
    # ВИПРАВЛЕНО: Беремо дані прямо з документа користувача, а не з teams_collection
    user = await users_collection.find_one({"telegram_id": str(callback.from_user.id)})
    if not user:
        await callback.answer("Помилка: не вдалося знайти ваші дані. Спробуйте перезайти.", show_alert=True)
        return

    budget = user.get('budget', 0)
    await callback.message.edit_text(f"🎟️ Ваш поточний баланс: **{budget}** купонів.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="captain_main_menu")]]))

# --- МОЇ МАТЕРІАЛИ ---
@router.callback_query(F.data == "captain_materials")
async def show_materials(callback: types.CallbackQuery):
    user = await users_collection.find_one({"telegram_id": str(callback.from_user.id)})
    if not user: return # Додаткова перевірка

    # ВИПРАВЛЕНО: Шукаємо замовлення по назві команди з документа користувача
    team_name = user.get("team_name")
    completed_orders = await orders_collection.find({"team_name": team_name, "status": "completed"}).to_list(length=None)
    
    owned_items = {}
    for order in completed_orders:
        for item in order['items']:
            owned_items[item['product_name']] = owned_items.get(item['product_name'], 0) + item['quantity']
            
    text = "📦 Список матеріалів вашої команди:\n\n" if owned_items else "📦 У вас ще немає матеріалів."
    for name, quantity in owned_items.items():
        text += f"🔹 **{name}** - {quantity} шт.\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="captain_main_menu")]]))

@router.callback_query(F.data == "captain_orders")
async def show_orders_history(callback: types.CallbackQuery):
    user = await users_collection.find_one({"telegram_id": str(callback.from_user.id)})
    if not user:
        return await callback.answer("Помилка: не вдалося знайти ваші дані.", show_alert=True)

    team_name = user.get("team_name")
    team_orders = await orders_collection.find({"team_name": team_name}).sort("created_at", -1).to_list(length=100)

    if not team_orders:
        return await callback.message.edit_text(
            "📜 У вас ще немає замовлень.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="captain_main_menu")]])
        )

    await callback.message.delete() # Видаляємо старе меню
    await callback.message.answer(f"📜 **Історія замовлень команди {team_name}:**", parse_mode="Markdown")

    for order in team_orders:
        date_str = order.get('created_at').strftime('%Y-%m-%d %H:%M') if order.get('created_at') else 'невідомо'
        status_text = STATUS_EMOJI.get(order.get('status'), 'Невідомо')
        
        order_details = f"**Замовлення №{order.get('order_number')}** від {date_str}\nСтатус: {status_text}\n"
        if order.get('status') == 'rejected' and order.get('rejection_reason'):
            order_details += f"Причина відхилення: *{order['rejection_reason']}*\n"
        
        order_details += "Склад:\n"
        for item in order.get('items', []):
            order_details += f" - {item.get('product_name')}: {item.get('quantity')} шт.\n"

        keyboard = None
        # Якщо замовлення готове до видачі, додаємо кнопку підтвердження
        if order.get('status') == 'approved':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👌🏻 Підтвердити отримання", callback_data=f"confirm_receipt_{order['_id']}")]
            ])
        
        await callback.message.answer(order_details, reply_markup=keyboard, parse_mode="Markdown")
        
    # Додаємо кнопку "Назад" останнім повідомленням
    await callback.message.answer("---", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад до гол. меню", callback_data="captain_main_menu")]]))

@router.callback_query(F.data.startswith("confirm_receipt_"))
async def confirm_receipt(callback: types.CallbackQuery, state: FSMContext):
    order_id = ObjectId(callback.data.split("_")[-1])
    
    updated_order = await orders_collection.find_one_and_update(
        {"_id": order_id, "status": "approved"},
        {"$set": {"status": "completed"}},
        return_document=True
    )

    if not updated_order:
        return await callback.answer("Це замовлення вже було підтверджено або скасовано.", show_alert=True)

    await callback.message.edit_text(f"✅ Дякуємо за підтвердження отримання замовлення №{updated_order['order_number']}!")
    
    user = await users_collection.find_one({"telegram_id": str(callback.from_user.id)})
    await log_action(
        action="Order Receipt Confirmed",
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        team_name=user.get('team_name'),
        details=f"Order #{updated_order['order_number']}"
    )



# --- ОБМІН/ПОВЕРНЕННЯ/ДОПОМОГА ---
@router.callback_query(F.data == "captain_exchange")
async def show_exchange_info(callback: types.CallbackQuery):
    text = "🔄 Для обміну товару, будь ласка, зверніться до HelpDesk. Опишіть, що ви хочете обміняти."
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="captain_main_menu")]]))

@router.callback_query(F.data == "captain_return")
async def show_return_info(callback: types.CallbackQuery):
    text = "↩️ Для повернення товару, будь ласка, зверніться до HelpDesk. Опишіть, що ви хочете повернути."
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="captain_main_menu")]]))

@router.callback_query(F.data == "captain_help")
async def show_help(callback: types.CallbackQuery):
    try:
        instruction_file = FSInputFile("Інстукція Капітан.pdf")
        await callback.message.answer_document(instruction_file, caption="✏️ Цей файл допоможе розібратись з функціоналом бота")
    except FileNotFoundError:
        await callback.answer("Помилка: файл з інструкцією не знайдено.", show_alert=True)
