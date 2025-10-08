from motor.motor_asyncio import AsyncIOMotorClient
from config import load_config
from aiogram.exceptions import TelegramForbiddenError
import asyncio 

config = load_config()


client = AsyncIOMotorClient(config.mongo_uri)
db = client["td"]  

users_collection = db["users"]
products_collection = db["products"]
config_collection = db["shop_config"]

