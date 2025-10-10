from motor.motor_asyncio import AsyncIOMotorClient
from config import load_config_td
from aiogram.exceptions import TelegramForbiddenError
import asyncio 

config = load_config_td()


client = AsyncIOMotorClient(config.mongo_uri)
db = client["td"]  

users_collection = db["users"]
products_collection = db["products"]
config_collection = db["shop_config"]
teams_collection = db["teams"]
orders_collection = db["orders"]

async def is_team_exist(team_name: str) -> bool:
    # Шукаємо хоча б одного користувача з такою назвою команди
    user = await users_collection.find_one({"team_name": team_name})
    return user is not None

async def is_team_password_correct(team_name: str, password: str) -> bool:
    # Перевіряємо, чи існує користувач з такою командою І паролем
    user = await users_collection.find_one({"team_name": team_name, "team_password": password})
    return user is not None