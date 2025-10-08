from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.choices import captain_menu_kb
import re

from bot.utils.database import is_team_exist, is_team_password_correct

# It seems these imports are from your project structure.
# Make sure they are available in your actual project.
# from bot.keyboards.registration import get_uni_kb, main_menu_kb, get_course_kb, where_kb, get_reg_kb
# from bot.utils.database import save_user_data

router = Router()

def is_correct_text(text):
    text = text.strip()
    if not text:
        return False
    if len(text) > 30:
        return False
    return bool(re.search(r'[a-zA-Zа-яА-ЯіІїЇєЄґҐ]', text)) and not re.fullmatch(r'[\W_]+', text)

# Define states for the captain's login flow
class CaptainLogin(StatesGroup):
    team_name = State()
    password = State()

# This is the initial handler from your code.
# It's been modified to start the login process.
@router.message(F.text == "Командир команди")
async def captain_login_start(message: types.Message, state: FSMContext):
    """
    This handler starts the captain's login process.
    It asks for the team name and removes the main keyboard.
    """
    await state.set_state(CaptainLogin.team_name)
    await message.answer(
        "Введіть назву команди:",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(CaptainLogin.team_name)
async def process_team_name(message: types.Message, state: FSMContext):
    """
    This handler processes the entered team name.
    It should check if the team exists in your database.
    """
    team_name = message.text
    if await is_team_exist(team_name):
        await state.update_data(team_name=team_name)
        await state.set_state(CaptainLogin.password)
        await message.answer("Введіть пароль команди:")
    else:
        await message.answer("Такої команди не існує. Спробуйте знову.")

@router.message(CaptainLogin.password)
async def process_password(message: types.Message, state: FSMContext):
    """
    This handler processes the entered password.
    It verifies the password for the given team.
    """
    password = message.text
    user_data = await state.get_data()
    team_name = user_data.get("team_name")

    # !!! IMPORTANT: Replace this with your actual password verification !!!
    # Example check:
    # if await your_database_function_to_verify_password(team_name, password):
    if await is_team_password_correct(team_name, password):
        await state.clear()  # Clear the state on successful login

        # --- Send instruction file and menu ---
        
        # IMPORTANT: Make sure you have a file named 'instruction.pdf' in the root directory
        # of your bot, or provide the correct path.
        # try:
        #     instruction_file = FSInputFile("instruction.pdf")
        # except FileNotFoundError:
        #     await message.answer("Помилка: файл з інструкцією не знайдено.")
        #     return

        await message.answer(
            f"Вітаємо, командире {team_name}! Оберіть одну з дій:", 
            reply_markup=captain_menu_kb
        )
        # await message.answer_document(
        #     document=instruction_file,
        #     caption=f"Вітаємо, командире {team_name}! Цей файл - це інструкція до користування ботом. Оберіть одну з дій:",
        #     reply_markup=captain_menu_kb
        # )
    else:
        await message.answer("Помилка авторизації. Спробуйте знову.")
        # The user remains in the CaptainLogin.password state to allow another attempt.

# --- Placeholder Handlers for Inline Keyboard Buttons ---
# These handlers will catch the button presses from the captain's menu.
# You should replace the placeholder text with your actual logic.

@router.callback_query(F.data == "captain_coupons")
async def show_coupons(callback: types.CallbackQuery):
    await callback.message.answer("Тут буде відображено баланс ваших купонів.")
    await callback.answer()

@router.callback_query(F.data == "captain_materials")
async def show_materials(callback: types.CallbackQuery):
    await callback.message.answer("Тут будуть ваші матеріали.")
    await callback.answer()

@router.callback_query(F.data == "captain_shop")
async def show_shop(callback: types.CallbackQuery):
    await callback.message.answer("Ласкаво просимо до магазину!")
    await callback.answer()

# --- ДОДАНО НОВІ ОБРОБНИКИ ---

@router.callback_query(F.data == "captain_cart")
async def show_cart(callback: types.CallbackQuery):
    """Handles the 'Cart' button press."""
    await callback.message.answer("Це ваш кошик. Зараз тут порожньо.")
    await callback.answer()

@router.callback_query(F.data == "captain_orders")
async def show_orders(callback: types.CallbackQuery):
    """Handles the 'My Orders' button press."""
    await callback.message.answer("Тут ви можете переглянути історію своїх замовлень.")
    await callback.answer()

@router.callback_query(F.data == "captain_exchange")
async def show_exchange_info(callback: types.CallbackQuery):
    """Handles the 'Exchange' button press."""
    await callback.message.answer("Інформація про умови обміну товару.")
    await callback.answer()

@router.callback_query(F.data == "captain_return")
async def show_return_info(callback: types.CallbackQuery):
    """Handles the 'Return' button press."""
    await callback.message.answer("Інформація про умови повернення товару.")
    await callback.answer()

@router.callback_query(F.data == "captain_help")
async def show_help(callback: types.CallbackQuery):
    """Handles the 'How to use' button press."""
    await callback.message.answer("Тут буде детальна інструкція або посилання на неї.")
    await callback.answer()