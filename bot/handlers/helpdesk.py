import datetime
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from bson.objectid import ObjectId
from os import getenv

# Імпортуємо всі необхідні колекції
from bot.utils.td_dg import orders_collection, teams_collection, products_collection
from bot.keyboards.choices import get_helpdesk_menu_kb
from bot.utils.sheetslogger import log_action

router = Router()

# --- Стани (FSM) ---
class HelpDeskLogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

class RejectOrder(StatesGroup):
    waiting_for_reason = State()

async def refresh_orders_view(message: types.Message):
    await message.delete()
    await show_active_orders(message)

async def update_active_orders_view(message: types.Message):
    active_orders = await orders_collection.find(
        {"status": {"$in": ["new", "approved"]}}
    ).sort("created_at", 1).to_list(length=20)
    
    if not active_orders:
        return await message.edit_text("✅ Активних замовлень немає.", reply_markup=get_helpdesk_menu_kb())

    await message.edit_text(f"📝 **Активні замовлення (всього: {len(active_orders)}):**")
    
    for order in active_orders:
        status_emoji = "🕙" if order['status'] == 'new' else "✅"
        order_text = (f"{status_emoji} **Замовлення №{order['order_number']}** від команди **{order['team_name']}**\n"
                      f"Сума: {order['total_cost']} купонів\nСклад:\n")
        for item in order['items']:
            order_text += f"- {item['product_name']} x{item['quantity']} шт.\n"
        
        buttons = []
        if order['status'] == 'new':
            buttons.append(InlineKeyboardButton(text="✅ Готово", callback_data=f"hd_approve_{order['_id']}"))
            buttons.append(InlineKeyboardButton(text="❌ Відхилити", callback_data=f"hd_reject_{order['_id']}"))
        if order['status'] == 'approved':
             buttons.append(InlineKeyboardButton(text="📦 Видано", callback_data=f"hd_complete_{order['_id']}"))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await message.answer(order_text, reply_markup=keyboard, parse_mode="Markdown")

@router.message(F.text == "HelpDesk")
async def cmd_helpdesk_start(message: types.Message, state: FSMContext):
    await state.set_state(HelpDeskLogin.waiting_for_login)
    await message.answer("Введіть логін HelpDesk:", reply_markup=ReplyKeyboardRemove())

@router.message(HelpDeskLogin.waiting_for_login)
async def process_helpdesk_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await state.set_state(HelpDeskLogin.waiting_for_password)
    await message.answer("Введіть пароль HelpDesk:")

@router.message(HelpDeskLogin.waiting_for_password)
async def process_helpdesk_password(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    login, password = user_data.get("login"), message.text
    expected_login, expected_password = getenv("HELPDESK_LOGIN"), getenv("HELPDESK_PASSWORD")

    if login == expected_login and password == expected_password:
        await state.clear()
        
        await teams_collection.update_one(
            {"telegram_id": str(message.from_user.id)},
            {"$set": {
                "username": message.from_user.username,
                "telegram_id": str(message.from_user.id),
                "role": "helpdesk",
                "chat_id": message.chat.id
            }},
            upsert=True  
        )

        await message.answer("Вітаємо чемпіонів HelpDesk! Оберіть дію:", reply_markup=get_helpdesk_menu_kb())
        
        await log_action(
            action="HelpDesk Login",
            user_id=message.from_user.id,
            username=message.from_user.username,
            team_name="N/A" # У HelpDesk немає команди
        )
    else:
        await state.set_state(HelpDeskLogin.waiting_for_login)
        await message.answer("Помилка авторизації. Спробуйте знову.\n\nВведіть логін HelpDesk:")
        await log_action(
            action="Failed HelpDesk Login",
            user_id=message.from_user.id,
            username=message.from_user.username
        )

@router.callback_query(F.data == "hd_active_orders")
async def show_active_orders(callback: types.CallbackQuery):
    active_orders = await orders_collection.find(
        {"status": {"$in": ["new", "approved"]}}
    ).sort("created_at", 1).to_list(length=20)
    
    # Видаляємо попереднє повідомлення (головне меню), щоб уникнути накопичення
    try: await callback.message.delete()
    except Exception: pass
    
    if not active_orders:
        await callback.message.answer("✅ Активних замовлень немає.", reply_markup=get_helpdesk_menu_kb())
        return await callback.answer()

    await callback.message.answer(f"📝 **Активні замовлення (всього: {len(active_orders)}):**")
    
    for order in active_orders:
        status_emoji = "🕙 В очікуванні" if order['status'] == 'new' else "✅ Готово до видачі"
        order_text = (f"**Замовлення №{order['order_number']}** ({status_emoji})\n"
                      f"Команда: **{order['team_name']}**\n"
                      f"Сума: {order['total_cost']} купонів\nСклад:\n")
        for item in order['items']:
            order_text += f"- {item['product_name']} x{item['quantity']} шт.\n"
        
        buttons = []
        if order['status'] == 'new':
            buttons.append(InlineKeyboardButton(text="✅ Готово", callback_data=f"hd_approve_{order['_id']}"))
            buttons.append(InlineKeyboardButton(text="❌ Відхилити", callback_data=f"hd_reject_{order['_id']}"))
        if order['status'] == 'approved':
             buttons.append(InlineKeyboardButton(text="📦 Видано", callback_data=f"hd_complete_{order['_id']}"))

        await callback.message.answer(order_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[buttons]), parse_mode="Markdown")
        
    await callback.message.answer("---", reply_markup=get_helpdesk_menu_kb()) # Повертаємо головне меню в кінці
    await callback.answer()

# --- ДІЇ З ЗАМОВЛЕННЯМИ ---

# 1. Замовлення готове до видачі (✅ Готово)
@router.callback_query(F.data.startswith("hd_approve_"))
async def approve_order(callback: types.CallbackQuery, bot: Bot):
    order_id = ObjectId(callback.data.split("_")[-1])
    updated_order = await orders_collection.find_one_and_update(
        {"_id": order_id, "status": "new"}, {"$set": {"status": "approved"}}, return_document=True
    )
    if not updated_order: return await callback.answer("Це замовлення вже оброблено.", show_alert=True)

    await callback.answer(f"Замовлення №{updated_order['order_number']} готове до видачі.", show_alert=True)
    
    captain_id = updated_order['captain_telegram_id']
    text = f"✅ Ваше замовлення №{updated_order['order_number']} **готове**! Заберіть його у HelpDesk та підтвердіть отримання у розділі 'Мої замовлення'."
    try: await bot.send_message(captain_id, text, parse_mode="Markdown")
    except Exception as e: print(f"Помилка сповіщення: {e}")
    await log_action(...)
    
    # Оновлюємо список замовлень
    await show_active_orders(callback)


# 2. Відхилення замовлення (❌ Відхилити)
@router.callback_query(F.data.startswith("hd_reject_"))
async def reject_order_start(callback: types.CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[-1]
    order = await orders_collection.find_one({"_id": ObjectId(order_id), "status": "new"})
    if not order: return await callback.answer("Це замовлення вже оброблено.", show_alert=True)

    await state.set_state(RejectOrder.waiting_for_reason)
    await state.update_data(order_id_to_reject=order_id)
    await callback.message.answer("Введіть причину відхилення:")

@router.message(RejectOrder.waiting_for_reason)
async def process_rejection_reason(message: types.Message, state: FSMContext, bot: Bot):
    reason, data = message.text, await state.get_data()
    order_id = ObjectId(data.get("order_id_to_reject"))
    order = await orders_collection.find_one({"_id": order_id})
    if not order:
        await message.answer("Помилка: замовлення не знайдено.")
        return await state.clear()

    # Повернення ресурсів
    for item in order['items']:
        await products_collection.update_one({"_id": item['product_id']}, {"$inc": {"stock_quantity": item['quantity']}})
    await teams_collection.update_many({"team_name": order['team_name']}, {"$inc": {"budget": order['total_cost']}})
    
    await orders_collection.update_one({"_id": order_id}, {"$set": {"status": "rejected", "rejection_reason": reason}})
    
    captain_id = order['captain_telegram_id']
    text = f"❌ Ваше замовлення №{order['order_number']} було **відхилено**.\n**Причина:** {reason}"
    try: await bot.send_message(captain_id, text, parse_mode="Markdown")
    except Exception as e: print(f"Помилка сповіщення: {e}")

    await message.answer(f"Замовлення №{order['order_number']} відхилено. Причина: {reason}")
    await state.clear()
    
    # Після відхилення просто показуємо головне меню
    await message.answer("Повернення до головного меню...", reply_markup=get_helpdesk_menu_kb())


# 3. Ручне підтвердження видачі (📦 Видано)
@router.callback_query(F.data.startswith("hd_complete_"))
async def complete_order_manual(callback: types.CallbackQuery, bot: Bot):
    order_id = ObjectId(callback.data.split("_")[-1])
    updated_order = await orders_collection.find_one_and_update(
        {"_id": order_id, "status": "approved"},
        {"$set": {"status": "completed", "completed_at": datetime.datetime.now(datetime.timezone.utc)}},
        return_document=True
    )
    if not updated_order: return await callback.answer("Замовлення має бути у статусі 'Готово'.", show_alert=True)
    
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    await callback.answer(f"Замовлення №{updated_order['order_number']} видано о {timestamp}.", show_alert=True)
    await callback.message.delete()
    
    captain_id = updated_order['captain_telegram_id']
    text = f"📦 Ваше замовлення №{updated_order['order_number']} було видано та закрито HelpDesk."
    try: await bot.send_message(captain_id, text)
    except Exception as e: print(f"Помилка сповіщення: {e}")
    await update_active_orders_view(callback.message)
    await log_action("Order Completed (Manual)", callback.from_user.id, callback.from_user.username, updated_order['team_name'], f"Order #{updated_order['order_number']}")

@router.message(RejectOrder.waiting_for_reason)
async def process_rejection_reason(message: types.Message, state: FSMContext, bot: Bot):
    reason = message.text
    data = await state.get_data()
    order_id = ObjectId(data.get("order_id_to_reject"))
    
    # --- КРИТИЧНО ВАЖЛИВА ЧАСТИНА: ПОВЕРНЕННЯ РЕСУРСІВ ---
    order = await orders_collection.find_one({"_id": order_id})
    if not order:
        await message.answer("Помилка: замовлення не знайдено.")
        return await state.clear()

    # 1. Повертаємо товари на склад
    for item in order['items']:
        await products_collection.update_one(
            {"_id": item['product_id']},
            {"$inc": {"stock_quantity": item['quantity']}}
        )

    # 2. Повертаємо купони команді
    await teams_collection.update_many(
        {"team_name": order['team_name']},
        {"$inc": {"budget": order['total_cost']}}
    )

    # 3. Оновлюємо статус замовлення
    await orders_collection.update_one(
        {"_id": order_id},
        {"$set": {"status": "rejected", "rejection_reason": reason}}
    )

    await message.answer(f"Замовлення №{order['order_number']} відхилено. Причина: {reason}")
    
    # Сповіщення для капітана
    captain_id = order['captain_telegram_id']
    text = f"❌ Ваше замовлення №{order['order_number']} було відхилено.\n**Причина:** {reason}"
    try:
        await bot.send_message(captain_id, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Помилка відправки сповіщення: {e}")

    await log_action("Order Rejected", message.from_user.id, message.from_user.username, order['team_name'], f"Order #{order['order_number']}, Reason: {reason}")
    await state.clear()


# @router.callback_query(F.data == "hd_general_history")
# async def show_general_history(callback: types.CallbackQuery):
#     await callback.answer("Цей функціонал в розробці.", show_alert=True)

# @router.callback_query(F.data == "hd_team_history")
# async def show_team_history(callback: types.CallbackQuery):
#     await callback.answer("Цей функціонал в розробці.", show_alert=True)

# @router.callback_query(F.data == "hd_stock_view")
# async def show_stock_view(callback: types.CallbackQuery):
#     await callback.answer("Цей функціонал в розробці.", show_alert=True)