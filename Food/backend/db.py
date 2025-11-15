# Food/backend/db.py
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb+srv://Atabek_2005:Atabek_2005@cluster0.zl0gpex.mongodb.net/"
client = AsyncIOMotorClient(MONGO_URI)

db = client["calorie-calculator"]

users_collection = db["users"]
# history_collection = db["history"]
foods_collection = db["food"]
food_logs_collection = db["food_logs"]
# settings_collection = db["settings"]
print(users_collection.find_one())