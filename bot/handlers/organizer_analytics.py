# bot/handlers/admin/analytics_handlers.py
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.td_dg import orders_collection, teams_collection, products_collection

router = Router()

def get_analytics_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Кількість проданих одиниць", callback_data="analytics_sold_units")],
        [InlineKeyboardButton(text="💸 Середні витрати купонів", callback_data="analytics_avg_spent")],
        [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu_back")]
    ])

@router.callback_query(F.data == "admin_view_analytics")
async def analytics_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("📊 Перегляд аналітики\n\nОберіть показник:", reply_markup=get_analytics_menu_kb())

@router.callback_query(F.data == "analytics_sold_units")
async def show_sold_units(callback: types.CallbackQuery):
    # УВАГА: Цей код запрацює, коли у вас буде колекція 'orders' з документами
    # формату: { ..., status: "completed", items: [{product_id: ..., quantity: ...}] }
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.product_id", "total_sold": {"$sum": "$items.quantity"}}},
        {"$sort": {"total_sold": -1}}
    ]
    sold_items_cursor = orders_collection.aggregate(pipeline)
    sold_items = await sold_items_cursor.to_list(length=None)

    if not sold_items:
        await callback.answer("Даних про продажі ще немає.", show_alert=True)
        return

    response_text = "📈 Продано одиниць:\n\n"
    for item in sold_items:
        product = await products_collection.find_one({"_id": item['_id']})
        product_name = product['name'] if product else "Невідомий товар"
        response_text += f"**{product_name}**: {item['total_sold']} шт.\n"
    
    await callback.message.edit_text(response_text, reply_markup=get_analytics_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "analytics_avg_spent")
async def show_avg_spent(callback: types.CallbackQuery):
    """
    Оновлена функція, яка рахує кількість унікальних команд з колекції 'users'.
    """
    # ВИПРАВЛЕНО: отримуємо список унікальних назв команд
    unique_teams_list = await teams_collection.distinct("team_name")
    total_teams = len(unique_teams_list)

    if total_teams == 0:
        await callback.answer("Не знайдено жодної команди для розрахунку.", show_alert=True)
        return
        
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total_spent": {"$sum": "$total_cost"}}} # Припускаємо, що є поле total_cost
    ]
    result_cursor = orders_collection.aggregate(pipeline)
    result = await result_cursor.to_list(length=1)
    
    total_spent = result[0]['total_spent'] if result else 0
    avg_spent = round(total_spent / total_teams, 2)
    
    response_text = f"💸 Середня кількість витрачених купонів на команду: **{avg_spent}** купонів."
    await callback.message.edit_text(response_text, reply_markup=get_analytics_menu_kb(), parse_mode="Markdown")