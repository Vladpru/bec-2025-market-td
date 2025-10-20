from motor.motor_asyncio import AsyncIOMotorClient
from config import load_config
from aiogram.exceptions import TelegramForbiddenError
import asyncio 

config = load_config()


client = AsyncIOMotorClient(config.mongo_uri, tz_aware=True)
db = client["bec-2025-bot-td"]  

teams_collection = db["teams"]
products_collection = db["products"]
config_collection = db["shop_config"]
orders_collection = db["orders"]
returns_log_collection = db["returns_log"]


async def is_team_exist(team_name: str) -> bool:
    # Шукаємо хоча б одного користувача з такою назвою команди
    user = await teams_collection.find_one({"team_name": team_name})
    return user is not None

async def is_team_password_correct(team_name: str, password: str) -> bool:
    # Перевіряємо, чи існує користувач з такою командою І паролем
    user = await teams_collection.find_one({"team_name": team_name, "team_password": password})
    return user is not None