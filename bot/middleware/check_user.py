from aiogram.dispatcher.middlewares.base import BaseMiddleware

class AuthMiddleware(BaseMiddleware):
    def __init__(self, db):
        super().__init__()
        self.db = db

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        user = await self.db.users_collection.find_one({"telegram_id": user_id})
        data["user"] = user
        return await handler(event, data)