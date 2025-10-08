# bot/handlers/admin.py

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.choices import get_admin_menu_kb
from os import getenv

# Імпортуємо наші колекції з бази даних
from bot.utils.database import products_collection, config_collection

router = Router()

# --- Стани (FSM) ---
class AdminLogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

# НОВІ СТАНИ для додавання товару
class AddProduct(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_quantity = State()

# --- Авторизація (ваш код, без змін) ---
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
    expected_login = getenv("ORGANIZER_LOGIN")
    expected_password = getenv("ORGANIZER_PASSWORD")
    if login == expected_login and password == expected_password:
        await state.clear()
        await message.answer("Вітаємо, Організатор! Оберіть одну з дій:", reply_markup=get_admin_menu_kb())
    else:
        await state.set_state(AdminLogin.waiting_for_login)
        await message.answer("Помилка авторизації. Спробуйте знову.\n\nВведіть логін Організатора:")


### БЛОК 1: КЕРУВАННЯ СТАНОМ МАГАЗИНУ ###

@router.callback_query(F.data == "admin_shop_on")
async def turn_shop_on(callback: types.CallbackQuery):
    # Оновлюємо документ в БД. upsert=True створить його, якщо він не існує.
    await config_collection.update_one(
        {"_id": "shop_status"}, 
        {"$set": {"is_open": True}}, 
        upsert=True
    )
    await callback.answer("✅ Магазин було увімкнено.", show_alert=True)

@router.callback_query(F.data == "admin_shop_off")
async def turn_shop_off(callback: types.CallbackQuery):
    await config_collection.update_one(
        {"_id": "shop_status"}, 
        {"$set": {"is_open": False}}, 
        upsert=True
    )
    await callback.answer("❌ Магазин було вимкнено.", show_alert=True)


### БЛОК 2: КЕРУВАННЯ ТОВАРАМИ (CRUD) ###

# Нове меню для керування товарами
def get_manage_items_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати товар", callback_data="admin_add_item")],
        [InlineKeyboardButton(text="📋 Переглянути товари", callback_data="admin_view_items")],
        # Тут згодом будуть кнопки "Редагувати" та "Видалити"
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu_back")]
    ])

# Замість заглушки тепер показуємо нове меню
@router.callback_query(F.data == "admin_manage_items")
async def manage_items(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Оберіть дію з товарами:", 
        reply_markup=get_manage_items_kb()
    )

# Повернення до головного меню адміністратора
@router.callback_query(F.data == "admin_menu_back")
async def admin_menu_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Вітаємо, Організатор! Оберіть одну з дій:",
        reply_markup=get_admin_menu_kb()
    )

# --- Перегляд товарів ---
@router.callback_query(F.data == "admin_view_items")
async def view_items(callback: types.CallbackQuery):
    # Знаходимо всі документи в колекції
    products_cursor = products_collection.find({})
    products_list = await products_cursor.to_list(length=100) # Обмеження на 100 товарів

    if not products_list:
        await callback.message.answer("Товарів ще немає.")
        return

    response_text = "📋 Список товарів:\n\n"
    for product in products_list:
        response_text += (
            f"🔹 **{product.get('name')}**\n"
            f"   Ціна: {product.get('price')} купонів\n"
            f"   Залишок: {product.get('quantity')} шт.\n\n"
        )
    
    await callback.message.answer(response_text, parse_mode="Markdown")
    await callback.answer()


# --- Додавання нового товару (початок FSM) ---
@router.callback_query(F.data == "admin_add_item")
async def add_item_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.waiting_for_name)
    await callback.message.answer("Введіть назву нового товару:")
    await callback.answer()

@router.message(AddProduct.waiting_for_name)
async def add_item_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.waiting_for_description)
    await message.answer("Тепер введіть опис товару:")

@router.message(AddProduct.waiting_for_description)
async def add_item_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProduct.waiting_for_price)
    await message.answer("Введіть ціну товару (тільки число):")

@router.message(AddProduct.waiting_for_price)
async def add_item_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Ціна повинна бути числом. Спробуйте ще раз.")
        return
    await state.update_data(price=int(message.text))
    await state.set_state(AddProduct.waiting_for_quantity)
    await message.answer("Введіть кількість товару на складі (тільки число):")

@router.message(AddProduct.waiting_for_quantity)
async def add_item_quantity(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Кількість повинна бути числом. Спробуйте ще раз.")
        return
    
    await state.update_data(quantity=int(message.text))
    
    # Збираємо всі дані та додаємо в БД
    product_data = await state.get_data()
    
    # Можна додати значення за замовчуванням
    product_data.setdefault("tier", "Uncategorized")
    product_data.setdefault("purchase_limit", 1)
    product_data.setdefault("is_active", True)
    
    await products_collection.insert_one(product_data)
    
    await message.answer(f"✅ Товар '{product_data['name']}' успішно додано!", reply_markup=get_admin_menu_kb())
    await state.clear()


# --- Інші обробники-заглушки ---
@router.callback_query(F.data == "admin_set_limits")
async def set_limits(callback: types.CallbackQuery):
    await callback.answer("Цей функціонал в розробці.", show_alert=True)

@router.callback_query(F.data == "admin_view_orders")
async def view_orders(callback: types.CallbackQuery):
    await callback.answer("Цей функціонал в розробці.", show_alert=True)

@router.callback_query(F.data == "admin_view_analytics")
async def view_analytics(callback: types.CallbackQuery):
    await callback.answer("Цей функціонал в розробці.", show_alert=True)