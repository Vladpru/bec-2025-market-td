# bot/handlers/helpdesk.py (ПОВНА ВЕРСІЯ З ІСТОРІЄЮ ТА ЗАЛИШКАМИ)

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

# Словник для красивого відображення статусів
STATUS_EMOJI = {
    "new": "🕙 В очікуванні",
    "approved": "✅ Готово до видачі",
    "rejected": "❌ Відхилено",
    "completed": "👌🏻 Видано"
}

# --- Стани (FSM) та Авторизація (без змін) ---
class HelpDeskLogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

class RejectOrder(StatesGroup):
    waiting_for_reason = State()
# ... (весь ваш код для авторизації залишається тут без змін)

# --- 1. ПЕРЕГЛЯД ЗАЛИШКІВ (МАГАЗИН) ---
@router.callback_query(F.data.startswith("hd_stock_view"))
async def show_stock_page(callback: types.CallbackQuery):
    try:
        page = int(callback.data.split("_")[-1])
    except ValueError:
        page = 1

    ITEMS_PER_PAGE = 10
    skip = (page - 1) * ITEMS_PER_PAGE
    
    total_items = await products_collection.count_documents({})
    products = await products_collection.find({}).sort("name", 1).skip(skip).limit(ITEMS_PER_PAGE).to_list(length=ITEMS_PER_PAGE)

    if not products:
        return await callback.answer("Товарів у базі немає.", show_alert=True)
        
    text = "🛍️ **Залишки товарів на складі:**\n\n"
    for p in products:
        text += f"🔹 **{p.get('name')}**: {p.get('stock_quantity', 0)} шт.\n"
        
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"hd_stock_view_{page-1}"))
    if total_items > page * ITEMS_PER_PAGE:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"hd_stock_view_{page+1}"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        nav_buttons,
        [InlineKeyboardButton(text="⬅️ До меню HelpDesk", callback_data="hd_main_menu_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# --- 2. ІСТОРІЯ ЗАМОВЛЕНЬ (ЗАГАЛЬНА) ---
@router.callback_query(F.data.startswith("hd_general_history"))
async def show_general_history_page(callback: types.CallbackQuery):
    try:
        page = int(callback.data.split("_")[-1])
    except ValueError:
        page = 1

    ITEMS_PER_PAGE = 5
    skip = (page - 1) * ITEMS_PER_PAGE
    
    total_orders = await orders_collection.count_documents({})
    all_orders = await orders_collection.find({}).sort("created_at", -1).skip(skip).limit(ITEMS_PER_PAGE).to_list(length=ITEMS_PER_PAGE)
    
    if not all_orders:
        return await callback.answer("Історія замовлень порожня.", show_alert=True)

    text = "📜 **Загальна історія замовлень:**\n\n---\n"
    for order in all_orders:
        date_str = (order.get('created_at') + datetime.timedelta(hours=3)).strftime('%d.%m %H:%M')
        status_text = STATUS_EMOJI.get(order.get('status'), 'Невідомо')
        text += (f"**№{order['order_number']}** ({date_str}) - **{order['team_name']}**\n"
                 f"Статус: {status_text}, Сума: {order['total_cost']}\n---\n")

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"hd_general_history_{page-1}"))
    if total_orders > page * ITEMS_PER_PAGE:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"hd_general_history_{page+1}"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        nav_buttons,
        [InlineKeyboardButton(text="⬅️ До меню HelpDesk", callback_data="hd_main_menu_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

# --- 3. ІСТОРІЯ ЗАМОВЛЕНЬ (ПО КОМАНДАХ) ---

# Крок 1: Вибір команди
@router.callback_query(F.data == "hd_team_history")
async def choose_team_for_history(callback: types.CallbackQuery):
    # Отримуємо список унікальних назв команд, які робили замовлення
    team_names = await orders_collection.distinct("team_name")
    
    if not team_names:
        return await callback.answer("Ще жодна команда не робила замовлень.", show_alert=True)

    buttons = [[InlineKeyboardButton(text=name, callback_data=f"hd_th_{name}")] for name in sorted(team_names)]
    buttons.append([InlineKeyboardButton(text="⬅️ До меню HelpDesk", callback_data="hd_main_menu_back")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("👥 Оберіть команду для перегляду історії:", reply_markup=keyboard)

# Крок 2: Відображення історії для обраної команди
@router.callback_query(F.data.startswith("hd_th_"))
async def show_team_history_page(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    team_name = parts[2]
    page = int(parts[3]) if len(parts) > 3 else 1
    
    ITEMS_PER_PAGE = 5
    skip = (page - 1) * ITEMS_PER_PAGE

    db_filter = {"team_name": team_name}
    total_orders = await orders_collection.count_documents(db_filter)
    team_orders = await orders_collection.find(db_filter).sort("created_at", -1).skip(skip).limit(ITEMS_PER_PAGE).to_list(length=ITEMS_PER_PAGE)

    text = f"📜 **Історія замовлень команди {team_name}:**\n\n"
    for order in team_orders:
        date_str = (order.get('created_at') + datetime.timedelta(hours=3)).strftime('%d.%m %H:%M')
        status_text = STATUS_EMOJI.get(order.get('status'), 'Невідомо')
        text += (f"**№{order['order_number']}** ({date_str}) - Статус: {status_text}\n"
                 f"Сума: {order['total_cost']} купонів\nСклад:\n")
        for item in order['items']:
            text += f" - {item['product_name']} x{item['quantity']} шт.\n"
        text += "---\n"

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"hd_th_{team_name}_{page-1}"))
    if total_orders > page * ITEMS_PER_PAGE:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"hd_th_{team_name}_{page+1}"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        nav_buttons,
        [InlineKeyboardButton(text="⬅️ Назад до вибору команди", callback_data="hd_team_history")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")


# --- Кнопка повернення в головне меню HelpDesk ---
@router.callback_query(F.data == "hd_main_menu_back")
async def back_to_hd_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Вітаємо чемпіонів HelpDesk! Оберіть дію:", reply_markup=get_helpdesk_menu_kb())