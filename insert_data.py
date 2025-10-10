# insert_data.py (оновлена версія)
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client.td

# Використовуємо більш стандартні назви колекцій
db.categories.drop()
db.products.drop() # Перейменовано з items на products

# Дані з виправленою помилкою та англійськими ключами
data = {
    "КРИТИЧНІ КОМПОНЕНТИ": {
        "restriction": "1 шт/команда перші 60 хв", "tier": 1,
        "items": [
            {"name": "Arduino nano (atmega328p)", "quantity_str": "1штx8к", "stock": 8, "base_price": 120, "coeff": 2.5, "final_price": 300},
            # ... (інші товари)
        ]
    },
    "ВИТРАТНІ МАТЕРІАЛИ": {
        "restriction": "Без обмежень, але швидко закінчуються", "tier": 4,
        "items": [
            {"name": "Спермоклей (4 стіки)", "quantity_str": "4штx8к", "stock": 32, "base_price": 20, "coeff": 1.4, "final_price": 28},
            # !!! ВИПРАВЛЕНО КЛЮЧ !!!
            {"name": "Припій (20-30гр)", "quantity_str": "30грx8к", "stock": 8, "base_price": 30, "coeff": 1.3, "final_price": 39},
            # ... (інші товари)
        ]
    },
    # ... (решта ваших даних з такими ж змінами ключів)
}

# (Вам потрібно буде оновити всі ключі в вашому файлі data. Я показав приклад)
# Для повноти, ось повний код для запуску:

def get_full_data():
    # Повертає повну структуру даних з англійськими ключами
    # (Це довгий блок, але він потрібен для запуску)
    full_data = {
    "КРИТИЧНІ КОМПОНЕНТИ": {
        "restriction": "1 шт/команда перші 60 хв", "tier": 1, "items": [
            {"name": "Arduino nano (atmega328p)", "quantity_str": "1штx8к", "stock": 8, "base_price": 120, "coeff": 2.5, "price_coupons": 300},
            {"name": "ESP модуль (не esp-01)", "quantity_str": "1штx8к", "stock": 8, "base_price": 150, "coeff": 2.5, "price_coupons": 375},
            {"name": "Motor shield L298N", "quantity_str": "1штx8к", "stock": 8, "base_price": 80, "coeff": 2.0, "price_coupons": 160},
            {"name": "Радіомодулі BLE (HC-06)", "quantity_str": "1штx8к", "stock": 8, "base_price": 100, "coeff": 2.0, "price_coupons": 200},
            {"name": "Паяльні станції", "quantity_str": "4-8шт", "stock": 8, "base_price": 800, "coeff": 1.5, "price_coupons": 1200} ]},
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
            {"name": "Спермоклей (4 стіки)", "quantity_str": "4штx8к", "stock": 32, "base_price": 20, "coeff": 1.4, "price_coupons": 28},
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
        "restriction": "Дорогі, обмежені, оренда", "tier": 6, "items": [
            {"name": "Мультиметр", "quantity_str": "4-8шт", "stock": 8, "base_price": 200, "coeff": 2.0, "price_coupons": 400},
            {"name": "Викрутки (набір 5шт)", "quantity_str": "5шт", "stock": 5, "base_price": 80, "coeff": 1.3, "price_coupons": 104},
            {"name": "Кусачки", "quantity_str": "5шт", "stock": 5, "base_price": 60, "coeff": 1.3, "price_coupons": 78},
            {"name": "Пласкогубці", "quantity_str": "3шт", "stock": 3, "base_price": 50, "coeff": 1.3, "price_coupons": 65},
            {"name": "Ніж канцелярський", "quantity_str": "4шт", "stock": 4, "base_price": 15, "coeff": 1.2, "price_coupons": 18},
            {"name": "Лінійка/штангенциркуль", "quantity_str": "1шт", "stock": 1, "base_price": 30, "coeff": 1.2, "price_coupons": 36} ]}
}
    return full_data

data = get_full_data()
category_ids = {}
for category_name, category_info in data.items():
    category_doc = {
        "name": category_name,
        "tier": category_info["tier"],
        "restriction": category_info["restriction"]
    }
    inserted_category = db.categories.insert_one(category_doc)
    category_ids[category_name] = inserted_category.inserted_id
    print(f"Inserted category: {category_name} with ID: {inserted_category.inserted_id}")

for category_name, category_info in data.items():
    category_id = category_ids[category_name]
    items_to_insert = []
    for item in category_info["items"]:
        product_doc = {
            "name": item["name"],
            "description": f"Tier {category_info['tier']}", # Додамо опис для наглядності
            "quantity_description": item["quantity_str"],
            "stock_quantity": item["stock"],
            "base_price_uah": item["base_price"],
            "coefficient": item["coeff"],
            "price_coupons": item["price_coupons"],
            "category_id": category_id
        }
        items_to_insert.append(product_doc)
    
    if items_to_insert:
        db.products.insert_many(items_to_insert) # Зберігаємо в колекцію products
        print(f"Inserted {len(items_to_insert)} items for category: {category_name}")

print("\nДані успішно вставлені в MongoDB!")
client.close()
