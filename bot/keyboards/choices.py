from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

captain_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎟️ Баланс купонів", callback_data="captain_coupons")],
    [InlineKeyboardButton(text="📦 Мої матеріали", callback_data="captain_materials")],
    [InlineKeyboardButton(text="🛍️ Магазин", callback_data="captain_shop")],
    [InlineKeyboardButton(text="🛒 Кошик", callback_data="view_cart")],
    [InlineKeyboardButton(text="📜 Мої замовлення", callback_data="captain_orders")],
    [InlineKeyboardButton(text="↩ Повернення", callback_data="captain_return")],
    [InlineKeyboardButton(text="✏️ Як користуватись ботом", callback_data="captain_help")]
])

def get_helpdesk_menu_kb() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Активні замовлення", callback_data="hd_active_orders")],
        [InlineKeyboardButton(text="📜 Історія замовлень загальна", callback_data="hd_general_history")],
        [InlineKeyboardButton(text="👥 Історія замовлень по командах", callback_data="hd_team_history")],
        [InlineKeyboardButton(text="🛍️ Перегляд залишків (Магазин)", callback_data="hd_stock_view")],
        [InlineKeyboardButton(text="✏️ Змінити бюджет команди", callback_data="hd_change_team_budget")]
    ])
    return keyboard

def get_admin_menu_kb() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Керування товарами", callback_data="admin_manage_items")],
        # [InlineKeyboardButton(text="⏱️ Встановлення обмежень", callback_data="admin_set_limits")],
        [InlineKeyboardButton(text="📊 Перегляд аналітики", callback_data="admin_view_analytics")],
        [InlineKeyboardButton(text="⏳ Керування фазами гри", callback_data="admin_set_phase")],
        # [InlineKeyboardButton(text="🔄 Перерахувати ціни (динаміка)", callback_data="admin_recalculate_prices")],
        [
            InlineKeyboardButton(text="🏪 Увімкнути магазин", callback_data="admin_shop_on"),
            InlineKeyboardButton(text="❌ Вимкнути магазин", callback_data="admin_shop_off")
        ]
    ])
    return keyboard