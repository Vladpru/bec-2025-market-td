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


async def check_order_cooldown(team_name: str) -> tuple[bool, str]:
    """
    Перевіряє ТІЛЬКИ інтервал між замовленнями для команди.
    ВИПРАВЛЕНО: Коректно працює з часовими зонами (UTC).
    """
    config = await get_shop_config()
    interval_minutes = config["purchase_interval_minutes"]
    
    last_order = await orders_collection.find_one({"team_name": team_name}, sort=[("created_at", -1)])
    
    if last_order:
        last_order_time = last_order["created_at"]
        
        # --- ОСНОВНЕ ВИПРАВЛЕННЯ ---
        # Використовуємо "свідомий" час UTC, щоб уникнути конфлікту часових зон.
        current_time = datetime.datetime.now(timezone.utc)
        # --- КІНЕЦЬ ВИПРАВЛЕННЯ ---

        time_passed = current_time - last_order_time
        required_interval = datetime.timedelta(minutes=interval_minutes)
        
        if time_passed < required_interval:
            time_to_wait = required_interval - time_passed
            remaining_seconds = time_to_wait.total_seconds()
            
            # Покращений вивід часу для користувача
            if remaining_seconds > 60:
                remaining_minutes = int(remaining_seconds // 60)
                remaining_sec_part = int(remaining_seconds % 60)
                return False, f"Занадто часті покупки. Зачекайте"
            else:
                return False, f"Занадто часті покупки. Зачекайте"
            
    return True, "OK"

async def check_item_rules(product_id, quantity: int) -> tuple[bool, str]:
    """
    Перевіряє правила, що стосуються КОНКРЕТНОГО товару (фази, ліміти).
    БЕЗ перевірки інтервалу між замовленнями.
    """
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
            
    if quantity > config["quantity_limit"]:
        return False, f"Заборонено купувати більше {config['quantity_limit']} одиниць товару за раз."

    return True, "OK"
