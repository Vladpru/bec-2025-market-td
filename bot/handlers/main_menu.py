from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, FSInputFile
from bot.keyboards.team import get_have_team_kb
from bot.keyboards.no_team import get_not_team_kb
from bot.keyboards.registration import main_menu_kb
from bot.utils.database import get_user

router = Router()

@router.message(F.text=="Пошук команди🔍")
async def get_link(message: types.Message, state: FSMContext):
    await state.clear()
    photo_path = "assets/find_team.png"
    photo_to_send = FSInputFile(photo_path)
    await message.answer_photo(
        photo=photo_to_send,
        caption=f"Не маєш команди? Не біда! Доєднайся в телеграм-чат та знайди її! Ось посилання:<a href='https://t.me/+EqpOjlPkgRtjYmEy'>Приєднатися</a>",
        parse_mode="HTML"
    )

@router.message(F.text=="Назад до головного меню🏠")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Повертаємося до головного меню...", reply_markup=main_menu_kb())

@router.message(F.text=="Моя команда🏆")
async def get_team(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        user_id = message.from_user.id
        if not user_id:
            await message.answer("⚠️ Не вдалося знайти твої дані. Спробуй ще раз пізніше.")
            return
        
        user_data = await get_user(user_id)
        if not user_data:
            await message.answer("⚠️ Не вдалося знайти твої дані. Спробуй ще раз пізніше.")
            return
        
        
        team_status = user_data.get('team','-')
        if team_status != '-':
            await message.answer_photo(
                photo=FSInputFile("assets/team.png"),
                caption=' В тебе вже є команда! ',
                parse_mode="HTML",
                reply_markup=get_have_team_kb()
            )
        else:
            await message.answer_photo(
                photo=FSInputFile("assets/team.png"),
                caption=' В тебе ще нема команди!\nЩоб взяти участь у змаганнях тобі потрібна команда! Вона повинна складатися з 4 учасників. Маєш свою непереможну четвірку? ',
                parse_mode="HTML",
                reply_markup=get_not_team_kb()
            )
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        await message.answer("An error occurred")
        await state.clear()

