from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Переключити секцію"),
                KeyboardButton(text="Розсилка")
            ],
            [
                KeyboardButton(text="Робота з командами"),
                KeyboardButton(text="Вийти з адмінки")
            ],
            [
                KeyboardButton(text="Завантажити всі CV"),
                KeyboardButton(text="Юзери без CV")
            ],
            [
                KeyboardButton(text="Нетворкінг Спід Дейтінг")
            ],
            [
                KeyboardButton(text="Присвоїти номера"),
                KeyboardButton(text="Speed Dating"),
            ]
        ],
        resize_keyboard=True
    )


def get_stage_selection_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Початок реєстрації"),
             KeyboardButton(text="Реєстрація")],
            [KeyboardButton(text="Підготовка до івенту"),
             KeyboardButton(text="Івент")],
            [KeyboardButton(text="Після івенту"),
             KeyboardButton(text="Тестове")],
            [KeyboardButton(text="Скасувати зміну стадії")]
        ],
        resize_keyboard=True
    )


def get_team_actions_inline_keyboard(team_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Показати учасників", callback_data=f"team:members:{team_id}"),
                InlineKeyboardButton(text="Показати репо", callback_data=f"team:repo:{team_id}")
            ],
            [
                InlineKeyboardButton(text="Завантажити CV", callback_data=f"team:cv:{team_id}"),
                InlineKeyboardButton(text="Показати технології", callback_data=f"team:tech:{team_id}")
            ],
            [
                InlineKeyboardButton(text="Апрувнути тестове", callback_data=f"team:approve_test:{team_id}"),
                InlineKeyboardButton(text="Апрувнути івент", callback_data=f"team:approve_event:{team_id}")
            ],
            [
                InlineKeyboardButton(text="Написати повідомлення", callback_data=f"team:message:{team_id}"),
                InlineKeyboardButton(text="Видалити команду", callback_data=f"team:delete:{team_id}")
            ],
            [
                InlineKeyboardButton(text="↩️ Повернутися до списку команд", callback_data="teams:return_list")
            ]
        ]
    )


def get_broadcast_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Усі користувачі", callback_data="broadcast:all")],
            [InlineKeyboardButton(text="Усі в командах", callback_data="broadcast:in_teams")],
            [InlineKeyboardButton(text="Усі не в командах", callback_data="broadcast:not_in_teams")],
            [InlineKeyboardButton(text="У командах менше 3 людей", callback_data="broadcast:teams_less_than_3")],
            [InlineKeyboardButton(text="У командах і допущені тестове",
                                  callback_data="broadcast:in_teams_passed_test")],
            [InlineKeyboardButton(text="У командах і не допущені до тестового",
                                  callback_data="broadcast:in_teams_not_passed_test")],
            [InlineKeyboardButton(text="У командах і допущені до івент",
                                  callback_data="broadcast:in_teams_approved_event")],
            [InlineKeyboardButton(text="У командах і не допущені до івенту",
                                  callback_data="broadcast:in_teams_not_approved_event")],
            [InlineKeyboardButton(text="Всім без CV", callback_data="broadcast:users_without_cv")],
            [
                InlineKeyboardButton(text="Команди HARD", callback_data="broadcast:hard")],
            [InlineKeyboardButton(text="Команди SOFT", callback_data="broadcast:soft")],
            [InlineKeyboardButton(text="Команди без категорії", callback_data="broadcast:no_category")
             ],
            [InlineKeyboardButton(text="Скасувати", callback_data="broadcast:cancel")]
        ]
    )