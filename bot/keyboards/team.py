from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_have_team_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Інформація про командуℹ️")], 
            [KeyboardButton(text="Тестове завдання")], 
            # [KeyboardButton(text="CV📜")],
            [KeyboardButton(text="Вийти з команди🚪")],
            [KeyboardButton(text="Назад до головного меню🏠")],
        ],
        resize_keyboard=True
    )

def get_back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )