# bot/handlers/admin/limits_handlers.py
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.td_dg import config_collection

router = Router()

class SetLimits(StatesGroup):
    waiting_for_quantity_limit = State()
    waiting_for_partial_time = State()
    waiting_for_full_time = State()
    waiting_for_interval = State()

def get_limits_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔢 На кількість виданих товарів", callback_data="limits_quantity")],
        [InlineKeyboardButton(text="⏰ На час покупки", callback_data="limits_time")],
        [InlineKeyboardButton(text="⏳ На інтервал між покупками", callback_data="limits_interval")],
        [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu_back")]
    ])

@router.callback_query(F.data == "admin_set_limits")
async def limits_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("⏱️ Встановлення обмежень\n\nОберіть тип обмеження:", reply_markup=get_limits_menu_kb())

# --- 1. Обмеження на кількість ---
@router.callback_query(F.data == "limits_quantity")
async def ask_quantity_limit(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SetLimits.waiting_for_quantity_limit)
    await callback.message.edit_text("Введіть максимальну кількість одиниць товару, яку команда може придбати за раз:")

@router.message(SetLimits.waiting_for_quantity_limit)
async def set_quantity_limit(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Помилка: введіть число.")
        return
    limit = int(message.text)
    await config_collection.update_one({"_id": "shop_limits"}, {"$set": {"quantity_per_purchase": limit}}, upsert=True)
    await state.clear()
    await message.answer(f"✅ Обмеження на кількість встановлено: {limit} одиниць.", reply_markup=get_limits_menu_kb())

# --- 2. Обмеження на час ---
@router.callback_query(F.data == "limits_time")
async def ask_time_limit(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SetLimits.waiting_for_partial_time)
    await callback.message.edit_text("Введіть час, з якого дозволено часткову купівлю (у хвилинах від початку гри):")

@router.message(SetLimits.waiting_for_partial_time)
async def set_partial_time(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Помилка: введіть число.")
        return
    await state.update_data(partial_time=int(message.text))
    await state.set_state(SetLimits.waiting_for_full_time)
    await message.answer("Тепер введіть час, з якого дозволено повну купівлю (у хвилинах від початку гри):")

@router.message(SetLimits.waiting_for_full_time)
async def set_full_time(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Помилка: введіть число.")
        return
    data = await state.get_data()
    partial_time = data.get("partial_time")
    full_time = int(message.text)
    
    await config_collection.update_one(
        {"_id": "shop_limits"}, 
        {"$set": {"partial_purchase_minutes": partial_time, "full_purchase_minutes": full_time}}, 
        upsert=True
    )
    await state.clear()
    await message.answer("✅ Часові обмеження встановлено.", reply_markup=get_limits_menu_kb())

# --- 3. Обмеження на інтервал ---
@router.callback_query(F.data == "limits_interval")
async def ask_interval_limit(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SetLimits.waiting_for_interval)
    await callback.message.edit_text("Введіть мінімальний інтервал між покупками для команди (у хвилинах):")

@router.message(SetLimits.waiting_for_interval)
async def set_interval_limit(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Помилка: введіть число.")
        return
    interval = int(message.text)
    await config_collection.update_one({"_id": "shop_limits"}, {"$set": {"purchase_interval_minutes": interval}}, upsert=True)
    await state.clear()
    await message.answer(f"✅ Обмеження на інтервал між покупками встановлено: {interval} хвилин.", reply_markup=get_limits_menu_kb())