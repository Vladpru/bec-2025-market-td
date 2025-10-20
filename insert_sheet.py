import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import asyncio

# --- Налаштування ---
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'techshop-469612-8d17d1de7962.json'  # Шлях до вашого файлу credentials.json
SPREADSHEET_TITLE = 'TD market products' # Назва вашої таблиці
WORKSHEET_NAME = 'Аркуш1' # Назва аркуша (зазвичай 'Sheet1' або 'Аркуш1')

def get_full_data():
    """Повертає повний словник з даними про товари."""
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
            # {"name": "Паяльні станції", "quantity_str": "4-8шт", "stock": 8, "base_price": 800, "coeff": 1.5, "price_coupons": 1200} ]},
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

    # Додаємо 'allowed_to_buy' до кожного товару
    for category in full_data.values():
        for item in category["items"]:
            item["allowed_to_buy"] = calculate_allowed_to_buy(item["stock"])

    return full_data

def update_spreadsheet():
    """Основна функція для оновлення Google таблиці."""
    try:
        # Авторизація
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        
        # Відкриття таблиці та аркуша
        spreadsheet = client.open(SPREADSHEET_TITLE)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        print(f"Успішно підключено до таблиці '{SPREADSHEET_TITLE}' та аркуша '{WORKSHEET_NAME}'.")

        # Отримання та форматування даних
        data = get_full_data()
        
        # Підготовка даних для запису
        rows_to_upload = []
        
        # Заголовки колонок
        headers = [
            "Категорія", "Назва товару", "Обмеження", "Рівень", 
            "Кількість (текст)", "На складі", "Базова ціна", 
            "Коефіцієнт", "Ціна в купонах", "Дозволено купити"
        ]
        rows_to_upload.append(headers)

        # Перетворення даних у формат для таблиці
        for category_name, category_data in data.items():
            # Додаємо рядок з назвою категорії як роздільник
            # Ми об'єднуємо комірки для цього рядка пізніше
            rows_to_upload.append([category_name.upper()]) 
            
            for item in category_data['items']:
                row = [
                    "", # Пуста комірка для категорії, бо вона вже є в рядку-роздільнику
                    item.get("name", ""),
                    category_data.get("restriction", ""),
                    category_data.get("tier", ""),
                    item.get("quantity_str", ""),
                    item.get("stock", ""),
                    item.get("base_price", ""),
                    item.get("coeff", ""),
                    item.get("price_coupons", ""),
                    item.get("allowed_to_buy", "")
                ]
                rows_to_upload.append(row)
        
        # Очищення аркуша перед записом нових даних
        print("Очищення аркуша...")
        worksheet.clear()
        
        # Запис всіх даних одним запитом
        print("Завантаження даних до таблиці...")
        worksheet.update('A1', rows_to_upload)
        
        # --- Опціонально: форматування ---
        # Об'єднання комірок для назв категорій
        print("Форматування таблиці...")
        current_row_index = 2 # Починаємо з другого рядка (після заголовків)
        for category_name in data.keys():
            worksheet.merge_cells(f'A{current_row_index}:J{current_row_index}')
            current_row_index += len(data[category_name]['items']) + 1 # +1 для самого рядка категорії
        
        print("\nГотово! Таблицю успішно оновлено.")

    except gspread.exceptions.SpreadsheetNotFound:
        print(f"ПОМИЛКА: Таблицю з назвою '{SPREADSHEET_TITLE}' не знайдено.")
        print("Перевірте, чи правильно вказана назва, та чи надали ви доступ сервісному акаунту.")
    except gspread.exceptions.WorksheetNotFound:
        print(f"ПОМИЛКА: Аркуш з назвою '{WORKSHEET_NAME}' не знайдено в таблиці '{SPREADSHEET_TITLE}'.")
    except FileNotFoundError:
        print(f"ПОМИЛКА: Файл '{CREDS_FILE}' не знайдено. Переконайтесь, що він знаходиться у тій самій папці, що і скрипт.")
    except Exception as e:
        print(f"Сталася невідома помилка: {e}")

# --- Запуск скрипта ---
if __name__ == "__main__":
    update_spreadsheet()