from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_uni_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎓 НУ “ЛП”"),
                KeyboardButton(text="🎓 ЛНУ ім. І. Франка"),
                KeyboardButton(text="🎓 УКУ"),
                KeyboardButton(text="🎓 Інший")
            ]
        ],
        resize_keyboard=True
    )


def get_course_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1 курс"), KeyboardButton(text="2 курс")],
            [KeyboardButton(text="3 курс"), KeyboardButton(text="4 курс")],
            [KeyboardButton(text="Магістратура")],
            [KeyboardButton(text="Не навчаюсь"), KeyboardButton(text="Інше")]
        ],
        resize_keyboard=True
    )

def where_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Так"), KeyboardButton(text="Ні")],
        ],
        resize_keyboard=True
    )

def get_phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
          [KeyboardButton(text="📱 Поділитись номером", request_contact=True)]  
        ],
        resize_keyboard=True
    )

def get_reg_kb():
    return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Зареєструватися на змагання💡")],
                [KeyboardButton(text="Пошук команди🔍")],
                [KeyboardButton(text="Детальніше про змагання🧐")]
            ],
            resize_keyboard=True
        )

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Командир команди")],
            [KeyboardButton(text="HelpDesk")],
            [KeyboardButton(text="Адміністратор")],
        ],
        resize_keyboard=True
    )

# ---------------------------------------------------- #
def hello_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Командир команди")],
            [KeyboardButton(text="HelpDesk")],
            [KeyboardButton(text="Організатор")],
        ],
        resize_keyboard=True
    )