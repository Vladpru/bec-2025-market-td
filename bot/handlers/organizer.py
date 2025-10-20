# bot/handlers/admin.py

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.choices import get_admin_menu_kb
from os import getenv
from bson.objectid import ObjectId # Важливо для роботи з ID з MongoDB

# Імпортуємо всі необхідні колекції
from bot.utils.td_dg import products_collection, config_collection, teams_collection, orders_collection

router = Router()

# --- Стани (FSM) ---
class AdminLogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    quantity = State()

class EditProduct(StatesGroup):
    choosing_field = State()
    waiting_for_new_value = State()

class DeleteProduct(StatesGroup):
    confirming_delete = State()

class SetLimits(StatesGroup):
    waiting_for_quantity_limit = State()
    waiting_for_partial_time = State()
    waiting_for_full_time = State()
    waiting_for_interval = State()

# Цей словник-мапа вирішує вашу проблему
FIELD_MAP = {
    "name": "name",
    "description": "description",
    "price": "base_price",  # <--- Ось тут ми вказуємо правильне поле для ціни
    "quantity": "stock_quantity" # <--- І тут для кількості, виходячи з вашої структури
}

# --- Авторизація (Без змін) ---
@router.message(F.text == "Організатор")
async def cmd_organizer_start(message: types.Message, state: FSMContext):
    await state.set_state(AdminLogin.waiting_for_login)
    await message.answer("Введіть логін Організатора:", reply_markup=ReplyKeyboardRemove())

@router.message(AdminLogin.waiting_for_login)
async def process_admin_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await state.set_state(AdminLogin.waiting_for_password)
    await message.answer("Введіть пароль Організатора:")

@router.message(AdminLogin.waiting_for_password)
async def process_admin_password(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    login = user_data.get("login")
    password = message.text
    expected_login, expected_password = getenv("ORGANIZER_LOGIN"), getenv("ORGANIZER_PASSWORD")
    if login == expected_login and password == expected_password:
        await state.clear()
        await message.answer("Вітаємо, Організатор! Оберіть одну з дій:", reply_markup=get_admin_menu_kb())
    else:
        await state.set_state(AdminLogin.waiting_for_login)
        await message.answer("Помилка авторизації. Спробуйте знову.\n\nВведіть логін Організатора:")

# --- Головне меню та повернення назад ---
@router.callback_query(F.data == "admin_menu_back")
async def admin_menu_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Вітаємо, Організатор! Оберіть одну з дій:", reply_markup=get_admin_menu_kb())

# --- БЛОК 1: КЕРУВАННЯ ТОВАРАМИ (CRUD) ---
def get_manage_items_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати товар", callback_data="crud_add_item")],
        [InlineKeyboardButton(text="✏️ Редагувати товар", callback_data="crud_edit_item_list")],
        [InlineKeyboardButton(text="🗑️ Видалити товар", callback_data="crud_delete_item_list")],
        [InlineKeyboardButton(text="📋 Переглянути всі товари", callback_data="crud_view_items")],
        [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu_back")]
    ])

@router.callback_query(F.data == "admin_manage_items")
async def manage_items_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ Керування товарами\n\nОберіть дію:", reply_markup=get_manage_items_kb())

# --- Початок блоку FSM для додавання товару ---

# 1. Початковий хендлер, який реагує на кнопку "➕ Додати товар"
@router.callback_query(F.data == "crud_add_item")
async def add_item_start(callback: types.CallbackQuery, state: FSMContext):
    """
    Починає процес додавання товару, встановлює перший стан (очікування назви)
    і просить користувача ввести назву.
    """
    await state.set_state(AddProduct.name)
    # Використовуємо edit_text, щоб змінити існуюче повідомлення з меню
    await callback.message.edit_text("Введіть назву товару:")
    await callback.answer()

# 2. Отримує назву товару, зберігає її і просить ввести опис
@router.message(AddProduct.name)
async def add_item_name(message: types.Message, state: FSMContext):
    """
    Обробляє введену назву, зберігає її у стані та переходить до наступного кроку.
    """
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("Введіть категорію товару (1-6):")

# 3. Отримує опис, зберігає і просить ввести ціну
@router.message(AddProduct.description)
async def add_item_tier(message: types.Message, state: FSMContext):
 
    await state.update_data(description="Tier " + message.text)
    await state.set_state(AddProduct.price)
    await message.answer("Введіть ціну товару (тільки число):")

# 4. Отримує ціну, валідує її, зберігає і просить ввести кількість
@router.message(AddProduct.price)
async def add_item_price(message: types.Message, state: FSMContext):
    """
    Обробляє ціну, перевіряє, чи є вона числом, і переходить до очікування кількості.
    """
    # Валідація: перевіряємо, чи ввів користувач число
    if not message.text.isdigit():
        await message.answer("Помилка: ціна повинна бути числом. Спробуйте ще раз.")
        return # Залишаємо користувача в поточному стані, щоб він міг виправити помилку
        
    await state.update_data(base_price=int(message.text)) # Зберігаємо як число
    await state.set_state(AddProduct.quantity)
    await message.answer("Введіть початкову кількість товару (тільки число):")

# 5. Отримує кількість, валідує, зберігає в БД і завершує процес
@router.message(AddProduct.quantity)
async def add_item_quantity(message: types.Message, state: FSMContext):
    """
    Останній крок. Обробляє кількість, збирає всі дані,
    записує їх в базу даних і очищує стан.
    """
    # Валідація: перевіряємо, чи ввів користувач число
    if not message.text.isdigit():
        await message.answer("Помилка: кількість повинна бути числом. Спробуйте ще раз.")
        return

    await state.update_data(stock_quantity=int(message.text), initial_stock_quantity=int(message.text)) # Зберігаємо як число
    
    # Отримуємо всі зібрані дані зі стану
    product_data = await state.get_data()
    
    # Для сумісності з вашою структурою, можна додати поля за замовчуванням
    # product_data.setdefault('base_price', product_data.p)
    product_data.setdefault('coefficient', 1.0)
    
    print(f"Дані для вставки в БД: {product_data}")

    try:
        # Записуємо фінальний документ в колекцію
        await products_collection.insert_one(product_data)
        
        # Очищуємо стан, завершуючи FSM
        await state.clear()
        
        # Повідомляємо користувача про успіх і показуємо головне адмін-меню
        await message.answer(
            f"✅ Товар '{product_data['name']}' успішно додано.",
            reply_markup=get_admin_menu_kb()
        )
    except Exception as e:
        print(f"!!! ПОМИЛКА при записі в MongoDB: {e}")
        await message.answer("Не вдалося додати товар через внутрішню помилку. Спробуйте пізніше.")
        await state.clear()


@router.callback_query(F.data == "crud_edit_item_list")
async def list_items_for_edit(callback: types.CallbackQuery, state: FSMContext):
    products = await products_collection.find({}).to_list(length=100)
    if not products:
        await callback.answer("Немає товарів для редагування.", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=p['name'], callback_data=f"edit_item_{p['_id']}")] for p in products
    ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage_items")]])
    await callback.message.edit_text("Оберіть товар для редагування:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("edit_item_"))
async def choose_edit_field(callback: types.CallbackQuery, state: FSMContext):
    product_id = callback.data.split("_")[2]
    product = await products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        await callback.answer("Товар не знайдено!", show_alert=True)
        return
    
    await state.update_data(product_id=product_id)
    await state.set_state(EditProduct.choosing_field)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назва", callback_data="edit_field_name")],
        [InlineKeyboardButton(text="Опис", callback_data="edit_field_description")],
        [InlineKeyboardButton(text="Ціна", callback_data="edit_field_price")],
        [InlineKeyboardButton(text="Кількість", callback_data="edit_field_quantity")],
        [InlineKeyboardButton(text="⬅️ Назад до списку", callback_data="crud_edit_item_list")]
    ])
    await callback.message.edit_text(f"Що ви хочете змінити для '{product['name']}'?", reply_markup=keyboard)

@router.callback_query(F.data.startswith("edit_field_"))
async def request_new_value(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[2] # "price", "quantity" і т.д.
    await state.update_data(field_to_edit=field)
    await state.set_state(EditProduct.waiting_for_new_value)
    await callback.message.edit_text(f"Введіть нове значення для поля '{field}':")


@router.message(EditProduct.waiting_for_new_value)
async def save_new_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id")
    # Отримуємо ключ поля з callback_data (наприклад, "price")
    field_key = data.get("field_to_edit") 
    new_value = message.text

    # Валідація
    if field_key in ["price", "quantity"] and not new_value.isdigit():
        await message.answer("Помилка: ціна та кількість повинні бути числами. Спробуйте ще раз.")
        return
    
    # Використовуємо мапу для отримання реального імені поля в БД
    db_field_name = FIELD_MAP.get(field_key)
    
    # Перевірка на випадок, якщо в мапі немає такого ключа
    if not db_field_name:
        await message.answer("Сталася внутрішня помилка: невідоме поле для редагування.")
        await state.clear()
        return

    update_value = int(new_value) if field_key in ["price", "quantity"] else new_value
    
    # Оновлюємо документ, використовуючи правильне ім'я поля з мапи
    await products_collection.update_one(
        {"_id": ObjectId(product_id)}, 
        {"$set": {db_field_name: update_value}}
    )
    
    product = await products_collection.find_one({"_id": ObjectId(product_id)})
    
    await state.clear()
    await message.answer(f"Товар '{product['name']}' успішно оновлено.", reply_markup=get_admin_menu_kb())

# 1.3 Видалення товару
@router.callback_query(F.data == "crud_delete_item_list")
async def list_items_for_delete(callback: types.CallbackQuery):
    products = await products_collection.find({}).to_list(length=100)
    if not products:
        await callback.answer("Немає товарів для видалення.", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=p['name'], callback_data=f"delete_item_{p['_id']}")] for p in products
    ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage_items")]])
    await callback.message.edit_text("Оберіть товар для видалення:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("delete_item_"))
async def confirm_delete(callback: types.CallbackQuery, state: FSMContext):
    product_id = callback.data.split("_")[2]
    product = await products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        await callback.answer("Товар не знайдено!", show_alert=True)
        return
        
    await state.update_data(product_id_to_delete=product_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Так, видалити", callback_data="delete_confirm_yes"),
            InlineKeyboardButton(text="❌ Ні, скасувати", callback_data="crud_delete_item_list")
        ]
    ])
    await callback.message.edit_text(f"Ви впевнені, що хочете видалити '{product['name']}'?", reply_markup=keyboard)

@router.callback_query(F.data == "delete_confirm_yes")
async def execute_delete(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id_to_delete")
    product = await products_collection.find_one({"_id": ObjectId(product_id)})
    await products_collection.delete_one({"_id": ObjectId(product_id)})
    await state.clear()
    await callback.message.edit_text(f"Товар '{product['name']}' успішно видалено.", reply_markup=get_admin_menu_kb())

# 1.4 Перегляд товарів
@router.callback_query(F.data == "crud_view_items")
async def view_items(callback: types.CallbackQuery):
    products = await products_collection.find({}).to_list(length=100)
    if not products:
        await callback.message.edit_text("Товарів ще немає.", reply_markup=get_manage_items_kb())
        return
    response_text = "📋 Список всіх товарів:\n\n"
    for p in products:
        response_text += (f"**{p.get('name')}**\n"
                          f"- Ціна: {p.get('base_price')}, Кількість: {p.get('quantity_description')}\n"
                          f"- Опис: {p.get('description')}\n---\n")
    await callback.message.edit_text(response_text, reply_markup=get_manage_items_kb(), parse_mode="Markdown")


# --- ПЕРЕРАХУВАННЯ ЦІН ---

async def update_all_prices():
    """
    Основна функція, яка проходить по всіх товарах і перераховує їх ціни.
    Повертає кількість оновлених товарів.
    """
    all_products = await products_collection.find({}).to_list(length=None)
    unique_teams_list = await teams_collection.distinct("team_name")
    total_teams = len(unique_teams_list)
    updated_count = 0

    for product in all_products:
        base_price = product.get('base_price', 0)
        coeff = product.get('coefficient', 1.0)
        new_price = base_price * coeff

        # 1. Механізм дефіциту
        initial_stock = product.get('initial_stock_quantity')
        current_stock = product.get('stock_quantity')
        if initial_stock and initial_stock > 0 and (current_stock / initial_stock) < 0.3:
            new_price *= 1.5  # +50% до ціни при дефіциті

        # 2. Механізм високого попиту
        if total_teams > 0:
            teams_bought_cursor = orders_collection.distinct(
                "team_name", 
                {"status": "completed", "items.product_id": product['_id']}
            )
            teams_bought = len(teams_bought_cursor)
            if (teams_bought / total_teams) > 0.5:
                new_price *= 1.3 # +30% до ціни при високому попиті

        # 3. Механізм кінця гри (поки не реалізовано, можна додати пізніше)

        final_price = round(new_price)
        
        # Оновлюємо ціну в БД, якщо вона змінилася
        if final_price != product.get('price_coupons'):
            await products_collection.update_one(
                {"_id": product['_id']},
                {"$set": {"price_coupons": final_price}}
            )
            updated_count += 1
            
    return updated_count

@router.callback_query(F.data == "admin_recalculate_prices")
async def recalculate_prices_handler(callback: types.CallbackQuery):
    await callback.answer("⏳ Починаю перерахунок цін, це може зайняти деякий час...", show_alert=False)
    
    try:
        updated_count = await update_all_prices()
        await callback.message.answer(f"✅ Перерахунок завершено! Оновлено цін: {updated_count}.")
    except Exception as e:
        print(f"Помилка при перерахунку цін: {e}")
        await callback.message.answer("❌ Сталася помилка під час перерахунку цін.")
