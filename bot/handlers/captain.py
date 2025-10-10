
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from bson.objectid import ObjectId

# Важливо: імпортуйте всі потрібні колекції та функції
from bot.utils.td_dg import (
    products_collection, teams_collection, users_collection, orders_collection, is_team_exist, is_team_password_correct
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

    if await is_team_password_correct(team_name, password):
        # Оновлюємо або створюємо запис для цього telegram_id
        await users_collection.update_one(
            {"telegram_id": str(message.from_user.id)}, # ВИПРАВЛЕНО: шукаємо по рядку
            {"$set": {"role": "captain", "username": message.from_user.username}},
            upsert=True # Створить користувача, якщо його немає
        )
        
        await state.clear()
        await message.answer(f"Вітаємо, командире {team_name}! Оберіть одну з дій:", reply_markup=captain_menu_kb)
        await log_action("Captain Login", message.from_user.id, f"Team: {team_name}")
    else:
        await message.answer("Помилка авторизації. Спробуйте знову.")
        await log_action("Failed Login Attempt", message.from_user.id, f"Team: {team_name}")

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
    await log_action("View Balance", callback.from_user.id, f"Budget: {budget}")

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
    await log_action("View Owned Materials", callback.from_user.id)

# --- ІСТОРІЯ ЗАМОВЛЕНЬ ---
@router.callback_query(F.data == "captain_orders")
async def show_orders_history(callback: types.CallbackQuery):
    user = await users_collection.find_one({"telegram_id": str(callback.from_user.id)})
    if not user: return

    # ВИПРАВЛЕНО: Шукаємо замовлення по назві команди
    team_name = user.get("team_name")
    team_orders = await orders_collection.find({"team_name": team_name}).sort("created_at", -1).to_list(length=100)

    if not team_orders:
        await callback.message.edit_text("📜 У вас ще немає замовлень.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="captain_main_menu")]]))
        return

    text = "📜 **Історія замовлень**\n\n"
    for order in team_orders:
        # УВАГА: Переконайтесь, що у вас є поле created_at при створенні замовлення
        date_str = order.get('created_at').strftime('%Y-%m-%d %H:%M') if order.get('created_at') else 'невідомо'
        status = order.get('status', 'невідомо')
        order_num = order.get('order_number', 'б/н')
        
        text += f"**Замовлення №{order_num}** від {date_str} - Статус: `{status}`\n"
        for item in order.get('items', []):
            text += f"   - {item.get('product_name')}: {item.get('quantity')} шт.\n"
        text += "---\n"

    # Тут можна додати пагінацію, якщо замовлень буде багато
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="captain_main_menu")]]))


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
        await log_action("Get Instructions", callback.from_user.id)
    except FileNotFoundError:
        await callback.answer("Помилка: файл з інструкцією не знайдено.", show_alert=True)
