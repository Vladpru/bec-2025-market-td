# bot/utils/shop_logic.py (ПОВНА СПРОЩЕНА ВЕРСІЯ)

from aiogram import types
from bot.handlers.helpdesk import show_active_orders
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.choices import get_helpdesk_menu_kb
from bot.utils.td_dg import config_collection, products_collection, orders_collection
import datetime
from datetime import timezone

PHASE_NAMES = {
    0: "Перегляд (0 хв)",
    1: "Часткова купівля (20 хв)",
    2: "Повна свобода (60 хв)"
}
STATUS_EMOJI = {
    "new": "🕙 В очікуванні",
    "approved": "✅ Готово до видачі",
    "rejected": "❌ Відхилено",
    "completed": "👌🏻 Отримано"
}


async def get_shop_config():
    """Отримує поточні налаштування магазину (статус та ліміти)."""
    status = await config_collection.find_one({"_id": "shop_status"}) or {}
    limits = await config_collection.find_one({"_id": "shop_limits"}) or {}
    return {
        "is_open": status.get("is_open", False),
        "phase": status.get("current_phase", 0),
        "quantity_limit": limits.get("quantity_per_purchase", 999),
        "purchase_interval_minutes": limits.get("purchase_interval_minutes", 5) 
    }

from bot.utils.td_dg import orders_collection # Переконайтесь, що імпорт є
from datetime import datetime, timedelta, timezone

async def check_order_cooldown(team_name: str):
    """
    Перевіряє, чи минув інтервал у 10 хвилин з моменту ОСТАННЬОГО УСПІШНОГО замовлення.
    Скасовані замовлення ігноруються.
    """
    shop_config = await config_collection.find_one({"_id": "shop_limits"}) or {}
    ORDER_INTERVAL_MINUTES = shop_config.get("purchase_interval_minutes", 4)

    # Шукаємо останнє замовлення зі статусом 'completed'
    last_completed_order = await orders_collection.find_one(
        {"team_name": team_name, "status": "completed"},
        sort=[("created_at", -1)]
    )

    if not last_completed_order:
        return True, "Дозволено, успішних замовлень ще не було."

    time_since_last_order = datetime.now(timezone.utc) - last_completed_order['created_at']
    
    if time_since_last_order < timedelta(minutes=ORDER_INTERVAL_MINUTES):
        remaining_time = timedelta(minutes=ORDER_INTERVAL_MINUTES) - time_since_last_order
        minutes, seconds = divmod(int(remaining_time.total_seconds()), 60)
        return False, f"Ви зможете зробити наступне замовлення через {minutes} хв {seconds} сек."
        
    return True, "Дозволено."

async def check_item_rules(product_id, quantity: int) -> tuple[bool, str]:
    config = await get_shop_config()
    product = await products_collection.find_one({"_id": product_id})

    if not config["is_open"]:
        return False, "Наразі магазин зачинено."
        
    phase = config["phase"]
    if phase == 0:
        return False, "Покупки заборонені, магазин працює в режимі перегляду."
    
    if phase == 1:
        tier_str = product.get("description", "")
        if any(t in tier_str for t in ["Tier 4", "Tier 5", "Tier 6"]):
            return False, f"Товар '{product['name']}' буде доступний для покупки на наступній фазі гри."
        if "Tier 1" in tier_str and quantity > 1:
            return False, "Для товарів Tier 1 можна придбати лише 1 одиницю на поточній фазі."
        if "Tier 2" in tier_str and quantity > 3:
            return False, "Для товарів Tier 2 можна придбати не більше 3 одиниць на поточній фазі."
        if "Tier 3" in tier_str and quantity > 3:
            return False, "Для товарів Tier 3 можна придбати не більше 3 одиниць на поточній фазі."

    elif phase == 2:
        allowed_quantity = product.get("allowed_to_buy")
        if allowed_quantity is not None and quantity > allowed_quantity:
            return False, f"Для товару '{product['name']}' можна придбати максимум {allowed_quantity} шт."

    return True, "OK"