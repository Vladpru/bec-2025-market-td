
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from config import load_config

def get_full_data():
    # ... Ваша функція get_full_data залишається без змін ...
    def calculate_allowed_to_buy(stock):
        if stock < 8: return 1
        elif stock < 16: return 2
        elif stock < 32: return 4
        elif stock < 64: return 6
        else: return 10

    full_data = {
    "КРИТИЧНІ КОМПОНЕНТИ": {
        "restriction": "1 шт/команда перші 60 хв", "tier": 1, "items": [
            {"name": "Arduino nano (atmega328p)", "quantity_str": "1штx8к", "stock": 8, "base_price": 120, "coeff": 2.5, "price_coupons": 300},
            {"name": "ESP модуль (не esp-01)", "quantity_str": "1штx8к", "stock": 8, "base_price": 150, "coeff": 2.5, "price_coupons": 375},
            {"name": "Motor shield L298N", "quantity_str": "1штx8к", "stock": 8, "base_price": 80, "coeff": 2.0, "price_coupons": 160},
            {"name": "Радіомодулі BLE (HC-06)", "quantity_str": "1штx8к", "stock": 8, "base_price": 100, "coeff": 2.0, "price_coupons": 200},
            ]},
    "ВАЖЛИВІ КОМПОНЕНТИ": {
        "restriction": "2-3 шт/команда перші 60 хв", "tier": 2, "items": [
            {"name": "Стабілізатори 5V (AMS1117)", "quantity_str": "2штx8к", "stock": 16, "base_price": 15, "coeff": 1.8, "price_coupons": 27},
            {"name": "Стабілізатори 3.3V (AMS1117)", "quantity_str": "2штx8к", "stock": 16, "base_price": 15, "coeff": 1.8, "price_coupons": 27},
            {"name": "Макетні плати 10x10см", "quantity_str": "1штx8к", "stock": 8, "base_price": 25, "coeff": 1.6, "price_coupons": 40},
            {"name": "DC-мотор з редуктором", "quantity_str": "4штx8к", "stock": 32, "base_price": 60, "coeff": 1.5, "price_coupons": 90},
            {"name": "Серво (дешеві сині)", "quantity_str": "1штx8к", "stock": 8, "base_price": 50, "coeff": 1.5, "price_coupons": 75},
            {"name": "Кроковий двигун + драйвер", "quantity_str": "1штx8к", "stock": 8, "base_price": 80, "coeff": 1.5, "price_coupons": 120},
            {"name": "Акуми Li-ion 18650", "quantity_str": "2штx8к", "stock": 16, "base_price": 80, "coeff": 1.4, "price_coupons": 112},
            {"name": "Холдери для акумів", "quantity_str": "1штx8к", "stock": 8, "base_price": 20, "coeff": 1.4, "price_coupons": 28} ]},
    "МАСОВІ КОМПОНЕНТИ": {
        "restriction": "Без обмежень після 20 хв", "tier": 3, "items": [
            {"name": "Резистори (набір 20шт)", "quantity_str": "2 набориx8к", "stock": 16, "base_price": 25, "coeff": 1.2, "price_coupons": 30},
            {"name": "Конденсатори 100-200μF", "quantity_str": "10штx8к", "stock": 80, "base_price": 5, "coeff": 1.3, "price_coupons": 7},
            {"name": "Діоди 1N4007", "quantity_str": "10штx8к", "stock": 80, "base_price": 10, "coeff": 1.2, "price_coupons": 12},
            {"name": "LED світлодіоди", "quantity_str": "5штx8к", "stock": 40, "base_price": 3, "coeff": 1.2, "price_coupons": 4},
            {"name": "Транзистори 2N2222 (PNP)", "quantity_str": "10штx8к", "stock": 80, "base_price": 15, "coeff": 1.2, "price_coupons": 18},
            {"name": "Транзистори 2N2222A (NPN)", "quantity_str": "10штx8к", "stock": 80, "base_price": 15, "coeff": 1.2, "price_coupons": 18},
            {"name": "LDR фоторезистори", "quantity_str": "3штx8к", "stock": 24, "base_price": 8, "coeff": 1.2, "price_coupons": 10},
            {"name": "Термістор NTC 10k", "quantity_str": "2штx8к", "stock": 16, "base_price": 6, "coeff": 1.2, "price_coupons": 8},
            {"name": "Бузер (пищалка)", "quantity_str": "1штx8к", "stock": 8, "base_price": 15, "coeff": 1.2, "price_coupons": 18},
            {"name": "Лазер 5mW", "quantity_str": "1штx8к", "stock": 8, "base_price": 25, "coeff": 1.3, "price_coupons": 33} ]},
    "ВИТРАТНІ МАТЕРІАЛИ": {
        "restriction": "Без обмежень, але швидко закінчуються", "tier": 4, "items": [
            {"name": "Термоклей (4 стіки)", "quantity_str": "4штx8к", "stock": 32, "base_price": 20, "coeff": 1.4, "price_coupons": 28},
            {"name": "Припій (20-30гр)", "quantity_str": "30грx8к", "stock": 8, "base_price": 30, "coeff": 1.3, "price_coupons": 39},
            {"name": "Каніфоль", "quantity_str": "4шт", "stock": 4, "base_price": 15, "coeff": 1.3, "price_coupons": 20},
            {"name": "Флюс (шприц)", "quantity_str": "1шт", "stock": 1, "base_price": 25, "coeff": 1.3, "price_coupons": 33},
            {"name": "Термоусадка 25см", "quantity_str": "25смx8к", "stock": 8, "base_price": 10, "coeff": 1.2, "price_coupons": 12},
            {"name": "Ізолента", "quantity_str": "1шт", "stock": 1, "base_price": 8, "coeff": 1.1, "price_coupons": 9},
            {"name": "Стяжки кабельні (100шт)", "quantity_str": "1-2п", "stock": 2, "base_price": 20, "coeff": 1.2, "price_coupons": 24} ]},
    "КОНСТРУКЦІЙНІ МАТЕРІАЛИ": {
        "restriction": "Доступні з початку в обмеженій кількості", "tier": 5, "items": [
            {"name": "Металеві прутки 50смx8к", "quantity_str": "50смx8к", "stock": 8, "base_price": 30, "coeff": 1.1, "price_coupons": 33},
            {"name": "Сталева проволока 100см", "quantity_str": "100смx8к", "stock": 8, "base_price": 15, "coeff": 1.1, "price_coupons": 17},
            {"name": "Мідна проволока 50см", "quantity_str": "50смx8к", "stock": 8, "base_price": 25, "coeff": 1.2, "price_coupons": 30},
            {"name": "Мідна проводка (4 жили)", "quantity_str": "100смx8к", "stock": 8, "base_price": 40, "coeff": 1.2, "price_coupons": 48},
            {"name": "Палиці 50см (до 10мм)", "quantity_str": "50смx8к", "stock": 8, "base_price": 20, "coeff": 1.1, "price_coupons": 22},
            {"name": "Шпажки (4 пачки)", "quantity_str": "4пачки", "stock": 4, "base_price": 25, "coeff": 1.1, "price_coupons": 28},
            {"name": "Фанера 3м²", "quantity_str": "3м²", "stock": 1, "base_price": 150, "coeff": 1.1, "price_coupons": 165} ]},
    "ІНСТРУМЕНТИ": {
        "restriction": "Дорогі, обмежені", "tier": 6, "items": [
            {"name": "Мультиметр", "quantity_str": "4-8шт", "stock": 8, "base_price": 200, "coeff": 2.0, "price_coupons": 400},
            {"name": "Викрутки (набір 5шт)", "quantity_str": "5шт", "stock": 5, "base_price": 80, "coeff": 1.3, "price_coupons": 104},
            {"name": "Кусачки", "quantity_str": "5шт", "stock": 5, "base_price": 60, "coeff": 1.3, "price_coupons": 78},
            {"name": "Пласкогубці", "quantity_str": "3шт", "stock": 3, "base_price": 50, "coeff": 1.3, "price_coupons": 65},
            {"name": "Ніж канцелярський", "quantity_str": "4шт", "stock": 4, "base_price": 15, "coeff": 1.2, "price_coupons": 18},
            {"name": "Лінійка/штангенциркуль", "quantity_str": "1шт", "stock": 1, "base_price": 30, "coeff": 1.2, "price_coupons": 36} ]}
    }
    for category in full_data.values():
        for item in category["items"]:
            item["allowed_to_buy"] = calculate_allowed_to_buy(item["stock"])
    return full_data

# --- ОСНОВНИЙ БЛОК СКРИПТУ ---
config = load_config()
client = None 

try:
    print(f"Спроба підключення до: {config.mongo_uri}") # <-- ДІАГНОСТИКА 1
    client = MongoClient(config.mongo_uri, tz_aware=True, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Підключення до MongoDB успішне!")
except ConnectionFailure as e:
    print(f"❌ Помилка підключення до MongoDB: {e}")
    exit()

db = client["bec-2025-bot-td"]
print("\nОчищення старих колекцій...")
db.categories.drop()
db.products.drop()
print("Старі колекції 'categories' та 'products' видалено.")

data = get_full_data()
category_ids = {}

print("\nВставка нових даних...")
for category_name, category_info in data.items():
    category_doc = {"name": category_name, "tier": category_info["tier"], "restriction": category_info["restriction"]}
    inserted_category = db.categories.insert_one(category_doc)
    category_ids[category_name] = inserted_category.inserted_id
    print(f"  -> Вставлено категорію: '{category_name}'")

for category_name, category_info in data.items():
    category_id = category_ids[category_name]
    items_to_insert = []
    for item in category_info["items"]:
        product_doc = {
            "name": item["name"], "description": f"Tier {category_info['tier']}",
            "quantity_description": item["quantity_str"], "stock_quantity": item["stock"],
            "allowed_to_buy": item["allowed_to_buy"], "base_price": item["base_price"],
            "coefficient": item["coeff"], "price_coupons": item["price_coupons"],
            "category_id": category_id
        }
        items_to_insert.append(product_doc)
    
    if items_to_insert:
        try:
            result = db.products.insert_many(items_to_insert)
            # <-- ДІАГНОСТИКА 2: Використовуємо результат операції для логування
            print(f"  -> Вставлено {len(result.inserted_ids)} товарів для категорії: '{category_name}'")
        except Exception as e:
            print(f"  -> !!! Помилка вставки для '{category_name}': {e}")


# --- ДІАГНОСТИКА 3: ФІНАЛЬНА ПЕРЕВІРКА ---
print("\n--- Фінальна перевірка ---")
try:
    category_count = db.categories.count_documents({})
    product_count = db.products.count_documents({})
    print(f"Знайдено документів в 'categories': {category_count}")
    print(f"Знайдено документів в 'products': {product_count}")

    if product_count > 0:
        print("✅ Дані успішно збережені та перевірені в базі даних.")
    else:
        print("⚠️ УВАГА: Колекція 'products' порожня. Перевірте URI підключення та права доступу.")
except Exception as e:
    print(f"❌ Помилка під час фінальної перевірки: {e}")


if client:
    client.close()
    print("\nЗ'єднання з MongoDB закрито.")