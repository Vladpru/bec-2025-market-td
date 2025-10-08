# bot/handlers/helpdesk.py

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.choices import get_helpdesk_menu_kb
from os import getenv

router = Router()

# Створюємо стани для процесу авторизації HelpDesk
class HelpDeskLogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

# Створюємо інлайн-клавіатуру для меню HelpDesk

@router.message(F.text == "HelpDesk")
async def cmd_helpdesk_start(message: types.Message, state: FSMContext):
    """
    Починає процес авторизації для HelpDesk.
    Запитує логін та переводить у стан очікування логіну.
    """
    await state.set_state(HelpDeskLogin.waiting_for_login)
    await message.answer(
        "Введіть логін HelpDesk:",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(HelpDeskLogin.waiting_for_login)
async def process_helpdesk_login(message: types.Message, state: FSMContext):
    """
    Отримує логін, зберігає його та запитує пароль.
    Переводить у стан очікування паролю.
    """
    # Зберігаємо введений логін у стані для подальшої перевірки
    await state.update_data(login=message.text)
    await state.set_state(HelpDeskLogin.waiting_for_password)
    await message.answer("Введіть пароль HelpDesk:")

@router.message(HelpDeskLogin.waiting_for_password)
async def process_helpdesk_password(message: types.Message, state: FSMContext):
    """
    Отримує пароль, перевіряє дані для авторизації.
    У разі успіху - показує меню. У разі невдачі - просить спробувати знову.
    """
    user_data = await state.get_data()
    login = user_data.get("login")
    password = message.text

    # !!! ВАЖЛИВО: Замініть цю перевірку на реальну логіку з вашою базою даних !!!
    # Це лише приклад-заглушка
    # Отримуємо логін та пароль з .env
    expected_login = getenv("HELPDESK_LOGIN")
    expected_password = getenv("HELPDESK_PASSWORD")

    if login == expected_login and password == expected_password:
        # У разі успішної авторизації - очищуємо стан
        await state.clear()
        await message.answer(
            "Вітаємо чемпіонів HelpDesk! Менюшка знизу, працюйте!",
            reply_markup=get_helpdesk_menu_kb()
        )
    else:
        # У разі невдалої авторизації - скидаємо процес і просимо почати знову
        await state.set_state(HelpDeskLogin.waiting_for_login)
        await message.answer(
            "Помилка авторизації. Спробуйте знову.\n\nВведіть логін HelpDesk:"
        )

# --- Обробники для кнопок меню HelpDesk ---

@router.callback_query(F.data == "hd_active_orders")
async def show_active_orders(callback: types.CallbackQuery):
    await callback.message.answer("Тут буде відображено список активних замовлень.")
    await callback.answer()

@router.callback_query(F.data == "hd_general_history")
async def show_general_history(callback: types.CallbackQuery):
    await callback.message.answer("Тут буде загальна історія всіх замовлень.")
    await callback.answer()

@router.callback_query(F.data == "hd_team_history")
async def show_team_history(callback: types.CallbackQuery):
    await callback.message.answer("Тут буде можливість переглянути історію замовлень по конкретних командах.")
    await callback.answer()

@router.callback_query(F.data == "hd_stock_view")
async def show_stock_view(callback: types.CallbackQuery):
    await callback.message.answer("Тут буде доступний перегляд залишків товарів у магазині.")
    await callback.answer()