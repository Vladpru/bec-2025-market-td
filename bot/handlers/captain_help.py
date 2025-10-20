from aiogram import F, Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from bot.handlers.captain_shop import CaptainActions 
from bot.utils.sheetslogger import log_action
from bot.utils.td_dg import teams_collection
from bot.keyboards.choices import captain_menu_kb

router = Router()

# --- 1. УНІВЕРСАЛЬНИЙ ОБРОБНИК СКАСУВАННЯ ---
@router.message(Command("cancel"))
@router.message(F.text.casefold() == "скасувати")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Дію скасовано. Повернення до головного меню.", reply_markup=captain_menu_kb)

# --- 2. ЗАПИТ НА ОБМІН ---
@router.callback_query(F.data == "captain_exchange")
async def request_exchange_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CaptainActions.writing_exchange_request)
    await state.update_data(message_to_delete=callback.message.message_id)
    
    await callback.message.edit_text(
        "🔄 **Запит на обмін**\n\n"
        "Опишіть одним повідомленням, що саме ви хочете обміняти і на що. Наприклад:\n"
        "`Обміняти 2 резистори на 1 стабілізатор 5V`\n\n"
        "Щоб скасувати, надішліть /cancel",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Скасувати", callback_data="captain_main_menu")]])
    )
    await callback.answer()

@router.message(CaptainActions.writing_exchange_request)
async def process_exchange_request(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_text = message.text
    
    # Очищуємо стан НЕГАЙНО, щоб уникнути повторних спрацювань
    await state.clear()
    
    try:
        message_id_to_delete = data.get("message_to_delete")
        if message_id_to_delete:
            await bot.delete_message(chat_id=message.chat.id, message_id=message_id_to_delete)

        user = await teams_collection.find_one({"telegram_id": str(message.from_user.id)})
        if not user:
            return await message.answer("Помилка: не вдалося знайти ваші дані. Спробуйте перезайти.")
            
        team_name = user.get("team_name", "Невідома команда")
        username = message.from_user.username or "N/A"

        # --- ОНОВЛЕНИЙ ТЕКСТ СПОВІЩЕННЯ ---
        helpdesk_message = (
            f"**🔄 Запит на ОБМІН**\n\n"
            f"**Від команди:** {team_name}\n"
            f"**Капітан:** @{username}\n\n"
            f"**Текст запиту:**\n"
            f"```{request_text}```\n\n"
            f"**Дія:** Зв'яжіться з капітаном для узгодження деталей обміну."
        )
        
        helpdesk_users = await teams_collection.find({"role": "helpdesk"}).to_list(length=None)
        if not helpdesk_users:
            print("ПОПЕРЕДЖЕННЯ: Не знайдено жодного користувача HelpDesk для сповіщення.")
        
        for hd_user in helpdesk_users:
            hd_telegram_id = hd_user.get("telegram_id")
            if hd_telegram_id:
                try:
                    await bot.send_message(int(hd_telegram_id), helpdesk_message, parse_mode="Markdown")
                except Exception as e:
                    print(f"Не вдалося надіслати сповіщення HelpDesk {hd_telegram_id}: {e}")

        await message.answer("✅ Ваш запит на обмін надіслано до HelpDesk. Очікуйте, з вами зв'яжуться.", reply_markup=captain_menu_kb)
        await log_action("Exchange Request", message.from_user.id, username, team_name, request_text)
        
    except Exception as e:
        print(f"Помилка під час обробки запиту на обмін: {e}")
        await message.answer("Сталася помилка під час надсилання запиту. Спробуйте ще раз.", reply_markup=captain_menu_kb)

# --- 3. ЗАПИТ НА ПОВЕРНЕННЯ ---
@router.callback_query(F.data == "captain_return")
async def request_return_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CaptainActions.writing_return_request)
    await state.update_data(message_to_delete=callback.message.message_id)
    
    await callback.message.edit_text(
        "↩️ **Запит на повернення**\n\n"
        "Опишіть одним повідомленням, що саме ви хочете повернути. Наприклад:\n"
        "`Повернути 1 Arduino nano, не підійшов`\n\n"
        "Щоб скасувати, надішліть /cancel",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Скасувати", callback_data="captain_main_menu")]])
    )
    await callback.answer()
@router.message(CaptainActions.writing_return_request)
async def process_return_request(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    request_text = message.text

    # Очищуємо стан НЕГАЙНО
    await state.clear()
    
    try:
        message_id_to_delete = data.get("message_to_delete")
        if message_id_to_delete:
            await bot.delete_message(chat_id=message.chat.id, message_id=message_id_to_delete)

        user = await teams_collection.find_one({"telegram_id": str(message.from_user.id)})
        if not user:
            return await message.answer("Помилка: не вдалося знайти ваші дані. Спробуйте перезайти.")
            
        team_name = user.get("team_name", "Невідома команда")
        username = message.from_user.username or "N/A"

        # --- ОНОВЛЕНИЙ ТЕКСТ СПОВІЩЕННЯ ---
        helpdesk_message = (
            f"**↩️ Запит на ПОВЕРНЕННЯ**\n\n"
            f"**Від команди:** {team_name}\n"
            f"**Капітан:** @{username}\n\n"
            f"**Текст запиту:**\n"
            f"```{request_text}```\n\n"
            f"**Дія:** Зв'яжіться з капітаном, щоб оглянути товар та узгодити повернення."
        )
        
        helpdesk_users = await teams_collection.find({"role": "helpdesk"}).to_list(length=None)
        if not helpdesk_users:
            print("ПОПЕРЕДЖЕННЯ: Не знайдено жодного користувача HelpDesk для сповіщення.")
        
        for hd_user in helpdesk_users:
            hd_telegram_id = hd_user.get("telegram_id")
            if hd_telegram_id:
                try:
                    await bot.send_message(int(hd_telegram_id), helpdesk_message, parse_mode="Markdown")
                except Exception as e:
                    print(f"Не вдалося надіслати сповіщення HelpDesk {hd_telegram_id}: {e}")

        await message.answer("✅ Ваш запит на повернення надіслано до HelpDesk. Очікуйте, з вами зв'яжуться.", reply_markup=captain_menu_kb)
        await log_action("Return Request", message.from_user.id, username, team_name, request_text)
    
    except Exception as e:
        print(f"Помилка під час обробки запиту на повернення: {e}")
        await message.answer("Сталася помилка під час надсилання запиту. Спробуйте ще раз.", reply_markup=captain_menu_kb)
    
# --- 4. ДОВІДКА ---

@router.callback_query(F.data == "captain_help")
async def show_help(callback: types.CallbackQuery):
    try:
        instruction_file = FSInputFile("Інстукція Капітан.pdf")
        await callback.message.answer_document(instruction_file, caption="✏️ Цей файл допоможе розібратись з функціоналом бота")
    except FileNotFoundError:
        await callback.answer("Помилка: файл з інструкцією не знайдено.", show_alert=True)