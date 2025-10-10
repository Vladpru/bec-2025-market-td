# bot/handlers/admin/shop_handlers.py
from aiogram import Router, types, F
from bot.utils.td_dg import config_collection

router = Router()

@router.callback_query(F.data == "admin_shop_on")
async def turn_shop_on(callback: types.CallbackQuery):
    """
    Обробляє натискання кнопки "Увімкнути магазин".
    Встановлює в базі даних is_open: true.
    """
    # Оновлюємо документ в БД. upsert=True створить його, якщо він ще не існує.
    await config_collection.update_one(
        {"_id": "shop_status"}, 
        {"$set": {"is_open": True}}, 
        upsert=True
    )
    
    # Показуємо спливаюче сповіщення про успіх
    await callback.answer("✅ Магазин було увімкнено.", show_alert=True)

@router.callback_query(F.data == "admin_shop_off")
async def turn_shop_off(callback: types.CallbackQuery):
    """
    Обробляє натискання кнопки "Вимкнути магазин".
    Встановлює в базі даних is_open: false.
    """
    await config_collection.update_one(
        {"_id": "shop_status"}, 
        {"$set": {"is_open": False}}, 
        upsert=True
    )
    
    # Показуємо спливаюче сповіщення про успіх
    await callback.answer("❌ Магазин було вимкнено.", show_alert=True)