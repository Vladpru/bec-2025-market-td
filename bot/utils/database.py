from motor.motor_asyncio import AsyncIOMotorClient
from config import load_config
from aiogram.exceptions import TelegramForbiddenError
import asyncio 

config = load_config()


client = AsyncIOMotorClient(config.mongo_uri)
db = client["bec-2025-bot"]  

users_collection = db["users"]
teams_collection = db["teams"]
cv_collection = db["cv"]

async def get_database():
    client = AsyncIOMotorClient(config.mongo_uri)
    db = client["bec-2025-bot"]
    return db

#------------------------------------------------------------------------------------------------

async def save_user_data(user_id, user_name, name, age, course, university, speciality, email, team):
    user_data = {
        "telegram_id": user_id,
        "username": user_name,
        "name": name,
        "age": age,
        "course": course,
        "university": university,
        "speciality": speciality,
        "email": email,
        "team": team,
        "cv_file_path": None,
    }

    await users_collection.update_one(
        {"telegram_id": user_id},  # Фільтр
        {"$set": user_data},       # Дані для оновлення
        upsert=True                # Додати документ, якщо він не існує
    )

#------------------------------------------------------------------------------------------------

async def save_team_data(team_id, team_name, category, password, members_telegram_ids):
    members = []
    for telegram_id in members_telegram_ids:
        user = await users_collection.find_one({"telegram_id": telegram_id})
        if user and "_id" in user:
            members.append(user["_id"])
    
    team_data = {
        "team_id": team_id,
        "team_name": team_name,
        "category": category,
        "password": password,
        "members": members,
        "is_participant": False,
        "test_task_status": False
    }
    teams_collection = db["teams"]
    await teams_collection.insert_one(team_data)

#------------------------------------------------------------------------------------------------

async def add_user(user_data: dict):
    existing = await users_collection.find_one({"telegram_id": user_data["telegram_id"]})
    if not existing:
        await users_collection.insert_one(user_data)

async def get_user(user_id):
    return await users_collection.find_one({"telegram_id": user_id})

async def get_team(user_id):
    user = await get_user(user_id)
    return await teams_collection.find_one({"members": user['_id']})

async def get_team_category(user_id):
    team = await get_team(user_id)
    if team:
        return team.get("category")

async def exit_team(user_id) -> bool:
    user = await get_user(user_id)
    if not user:
        return False
    
    user_object_id = user["_id"]
    telegram_id = user["telegram_id"] 

    current_team = await teams_collection.find_one({"members": user_object_id})
    if not current_team:
        current_user = await users_collection.find_one({"telegram_id": telegram_id})
        if current_user and current_user.get("team") != "-":
            await users_collection.update_one(
                {"telegram_id": telegram_id},
                {"$set": {"team": "-"}}
            )
        return 'already_out' 

    res = await teams_collection.update_one(
        {"_id": current_team["_id"]}, 
        {"$pull": {"members": user_object_id}}
    )
    
    if res.modified_count == 0: 
        return False
    
    await users_collection.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"team": "-"}}
    )
    
    updated_team = await teams_collection.find_one({"_id": current_team["_id"]})
    if updated_team and len(updated_team.get("members", [])) == 0:
        await teams_collection.delete_one({"_id": current_team["_id"]})
    
    return True

async def update_user_team(user_id, team_id):
    await users_collection.update_one(
        {"telegram_id": user_id},
        {"$set": {"team": team_id}},  
        upsert=True
    )  

#------------------------------------------------------------------------------------------------

async def get_cv(user_id: int):
    return await cv_collection.find_one({"telegram_id": user_id})

async def count_users():
    return await users_collection.count_documents({"registered": True})

async def get_all_users():
    return users_collection.find({})

async def get_all_users_with_cv():
    return users_collection.find({"cv_file_path": {"$ne": None}})

async def count_all_users():
    return await users_collection.count_documents({})

async def get_all_teams():
    return teams_collection.find({})

#------------------------------------------------------------------------------------------------

async def get_team_by_name(team_name):
    return await teams_collection.find_one({"team_name": team_name})

async def add_user_to_team(user_id, team_id):
    user = await users_collection.find_one({"telegram_id": user_id})
    team = await teams_collection.find_one({"team_id": team_id})
    if not user or not team:
        return False
    # Додаємо user до members, якщо його там ще нема
    if user["_id"] not in team["members"]:
        await teams_collection.update_one(
            {"team_id": team_id},
            {"$push": {"members": user["_id"]}}
        )
    # Оновлюємо поле team у user
    await users_collection.update_one(
        {"telegram_id": user_id},
        {"$set": {"team": team_id}}
    )
    return True

async def is_full_team(team_id):
    team = await teams_collection.find_one({"team_id": team_id})
    if not team:
        return False
    return len(team.get("members", [])) >= 4

#------------------------------------------------------------------------------------------------

async def is_user_in_team(user_id):
    user = await users_collection.find_one({"telegram_id": user_id})
    if not user:
        return False
    return user.get("team") not in ["-"]

async def get_team_by_user_id(user_id):
    user = await users_collection.find_one({"telegram_id": user_id})
    return await teams_collection.find_one({"members": user["_id"]})

async def is_user_registered(user_id):
    user = await users_collection.find_one({"telegram_id": user_id})
    return user is not None

#------------------------------------------------------------------------------------------------

async def get_all_user_ids() -> list[int]:
    cursor = users_collection.find({}, {"telegram_id": 1})
    return [int(doc["telegram_id"]) async for doc in cursor]

async def is_user_registered(user_id: int) -> bool:
    user = await users_collection.find_one({"telegram_id": user_id})
    return user is not None

async def is_user_have_cv(user_id: int) -> bool:
    user = await users_collection.find_one({"telegram_id": user_id})
    return user is not None and (user.get("cv_file_path") is not None and user.get("cv_file_path") != "null")

async def is_team_exist(team_name: str) -> bool:
    team = await teams_collection.find_one({"team_name": team_name})
    return team is not None
async def is_team_password_correct(team_name: str, password: str) -> bool:
    team = await teams_collection.find_one({"team_name": team_name, "password": password})
    return team is not None