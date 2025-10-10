# bot/handlers/admin/phase_handlers.py (ОНОВЛЕНА ВЕРСІЯ)

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.td_dg import config_collection

router = Router()

# Словник з назвами фаз для відображення
PHASE_NAMES = {
    0: "Перегляд (0 хв)",
    1: "Часткова купівля (20 хв)",
    2: "Повна свобода (60 хв)"
}

async def get_phase_menu_kb() -> tuple[str, InlineKeyboardMarkup]:
    """
    Повертає текст та клавіатуру на основі поточної фази гри в БД.
    """
    config = await config_collection.find_one({"_id": "shop_status"})
    current_phase = config.get("current_phase", 0) if config else 0
    
    text = (f"⚙️ **Керування фазами гри**\n\n"
            f"**Поточна фаза:** `{PHASE_NAMES.get(current_phase, 'Невідомо')}`\n\n"
            f"Оберіть, яку фазу встановити:")
    
    # Створюємо клавіатуру з трьома кнопками для кожної фази
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Фаза 0 (Тільки перегляд)", callback_data="set_phase_0")],
        [InlineKeyboardButton(text="➡️ Фаза 1 (Часткова купівля)", callback_data="set_phase_1")],
        [InlineKeyboardButton(text="➡️ Фаза 2 (Повна свобода)", callback_data="set_phase_2")],
        [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu_back")]
    ])
    return text, keyboard

@router.callback_query(F.data == "admin_set_phase")
async def phase_menu(callback: types.CallbackQuery):
    """
    Обробник для входу в меню керування фазами.
    """
    text, keyboard = await get_phase_menu_kb()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("set_phase_"))
async def set_phase_action(callback: types.CallbackQuery):
    """
    Обробляє натискання будь-якої кнопки зміни фази (0, 1 або 2).
    """
    # Витягуємо номер нової фази з callback_data (наприклад, '0' з 'set_phase_0')
    new_phase = int(callback.data.split("_")[-1])
    
    # Оновлюємо поле 'current_phase' в документі 'shop_status'
    await config_collection.update_one(
        {"_id": "shop_status"}, 
        {"$set": {"current_phase": new_phase}}, 
        upsert=True  # Створить документ, якщо його немає
    )
    
    await callback.answer(f"✅ Фазу гри змінено на '{PHASE_NAMES.get(new_phase)}'.", show_alert=True)
    
    # Оновлюємо повідомлення, щоб показати актуальний стан
    text, keyboard = await get_phase_menu_kb()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")