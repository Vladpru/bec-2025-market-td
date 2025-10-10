# bot/utils/shop_logic.py
from bot.utils.td_dg import config_collection, products_collection, orders_collection

PHASE_NAMES = {
    0: "Перегляд (0 хв)",
    1: "Часткова купівля (20 хв)",
    2: "Повна свобода (60 хв)"
}

async def get_shop_config():
    """Отримує поточні налаштування магазину (статус та ліміти)."""
    status = await config_collection.find_one({"_id": "shop_status"}) or {}
    limits = await config_collection.find_one({"_id": "shop_limits"}) or {}
    return {
        "is_open": status.get("is_open", False),
        "phase": status.get("current_phase", 0),
        "quantity_limit": limits.get("quantity_per_purchase", 999),
        # ... інші ліміти
    }

async def check_purchase_rules(product_id, quantity: int, team_name: str) -> tuple[bool, str]:
    """
    Головна функція перевірки. Повертає (Дозволено, Причина).
    """
    config = await get_shop_config()
    product = await products_collection.find_one({"_id": product_id})
    
    # 1. Перевірка, чи магазин відкритий
    if not config["is_open"]:
        return False, "Наразі магазин зачинено."

    # 2. Перевірка поточної фази гри
    phase = config["phase"]
    if phase == 0:
        return False, "Покупки заборонені, магазин працює в режимі перегляду."
    
    if phase == 1:
        # УВАГА: беремо Tier з поля description, як у вашій БД
        tier_str = product.get("description", "")
        
        if "Tier 1" in tier_str and quantity > 1:
            return False, f"Для товарів Tier 1 можна придбати лише 1 одиницю на поточній фазі."
        
        if "Tier 2" in tier_str and quantity > 3:
            return False, f"Для товарів Tier 2 можна придбати не більше 3 одиниць на поточній фазі."
            
        if any(t in tier_str for t in ["Tier 3", "Tier 4", "Tier 5", "Tier 6"]):
            return False, f"Товар '{product['name']}' буде доступний для покупки на наступній фазі гри."

    # 3. Перевірка загального ліміту на кількість за раз
    if quantity > config["quantity_limit"]:
        return False, f"Заборонено купувати більше {config['quantity_limit']} одиниць товару за раз."

    return True, "OK"