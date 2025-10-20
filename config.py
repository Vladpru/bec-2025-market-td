from dataclasses import dataclass
import os
import os

from dotenv import load_dotenv

# print("=== DEBUG ENV VARIABLES ===")
# print("BOT_TOKEN:", os.getenv("BOT_TOKEN"))
# print("ADMIN_ID:", os.getenv("ADMIN_ID"))
# print("ADMIN_START:", os.getenv("ADMIN_START"))
# print("DBMONGO_URL:", os.getenv("DBMONGO_URL"))
# print("===========================")

load_dotenv()

@dataclass
class Config:
    bot_token: str
    admin: str
    mongo_uri: str 

def load_config():
    return Config(
        bot_token=os.getenv("BOT_TOKEN"),
        admin=os.getenv("ADMIN_ID"),
        mongo_uri=os.getenv("DBMONGO_URL"),
        # mongo_uri=os.getenv("DBMONGO_URL_MARKET"),
    )

def load_config_td():
    return Config(
        bot_token=os.getenv("BOT_TOKEN"),
        admin=os.getenv("ADMIN_ID"),
        mongo_uri=os.getenv("DBMONGO_URL_MARKET"),
    )
