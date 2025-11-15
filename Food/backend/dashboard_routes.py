from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .db import food_logs_collection, foods_collection
from .security import decode_access_token
from .schemas_food_logs import FoodLogCreate

dashboard_router = APIRouter()
auth_scheme = HTTPBearer()


# ---------------------------
# Extract user from JWT token
# ---------------------------
async def get_user_id(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    jwt_token = token.credentials
    payload = decode_access_token(jwt_token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload["user_id"]


# ---------------------------
# POST /dashboard/log
# ---------------------------
@dashboard_router.post("/log")
async def log_food(data: FoodLogCreate, user_id: str = Depends(get_user_id)):

    food = await foods_collection.find_one({"_id": ObjectId(data.food_id)})
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    servings = data.servings

    log_entry = {
        "user_id": user_id,
        "food_id": ObjectId(data.food_id),
        "food_name": food["name"],

        # calculated values
        "calories": food["nutrition"]["calories"] * servings,
        "protein_g": food["nutrition"]["protein_g"] * servings,
        "fat_g": food["nutrition"]["fat_g"] * servings,
        "carbs_g": food["nutrition"]["carbohydrates_g"] * servings,

        "serving_size": data.serving_size,
        "image_url": data.image_url,
        "created_at": datetime.utcnow()
    }

    result = await food_logs_collection.insert_one(log_entry)

    # return saved log with string IDs
    saved = await food_logs_collection.find_one({"_id": result.inserted_id})
    saved["_id"] = str(saved["_id"])
    saved["food_id"] = str(saved["food_id"])

    return {"message": "Food logged", "log": saved}


# ---------------------------
# GET /dashboard/day
# ---------------------------
@dashboard_router.get("/day")
async def get_day_logs(date: str, user_id: str = Depends(get_user_id)):

    start = datetime.fromisoformat(date)
    end = start.replace(hour=23, minute=59, second=59)

    logs = await food_logs_collection.find({
        "user_id": user_id,
        "created_at": {"$gte": start, "$lte": end}
    }).to_list(None)

    # convert ObjectIds
    for log in logs:
        log["_id"] = str(log["_id"])
        log["food_id"] = str(log["food_id"])

    return {"date": date, "logs": logs}


# ---------------------------
# GET /dashboard/summary
# ---------------------------
@dashboard_router.get("/summary")
async def get_summary(date: str, user_id: str = Depends(get_user_id)):

    start = datetime.fromisoformat(date)
    end = start.replace(hour=23, minute=59, second=59)

    logs = await food_logs_collection.find({
        "user_id": user_id,
        "created_at": {"$gte": start, "$lte": end}
    }).to_list(None)

    summary = {"calories": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0}

    for log in logs:
        summary["calories"] += log["calories"]
        summary["protein_g"] += log["protein_g"]
        summary["fat_g"] += log["fat_g"]
        summary["carbs_g"] += log["carbs_g"]

    return {"date": date, "summary": summary}


# ---------------------------
# GET /dashboard/history
# ---------------------------
@dashboard_router.get("/history")
async def get_history(user_id: str = Depends(get_user_id)):

    logs = await food_logs_collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(50).to_list(None)

    # convert IDs for frontend
    for log in logs:
        log["_id"] = str(log["_id"])
        log["food_id"] = str(log["food_id"])

    return {"history": logs}

@dashboard_router.get("/chart")
async def get_chart(user_id: str = Depends(get_user_id)):
    """
    Returns last 7 days calories for charting:
    [
        {"date": "2025-11-10", "calories": 520},
        {"date": "2025-11-11", "calories": 320},
        ...
    ]
    """

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=6)

    # Fetch logs from last 7 days
    logs = await food_logs_collection.find({
        "user_id": user_id,
        "created_at": {"$gte": datetime.combine(start_date, datetime.min.time())}
    }).to_list(None)

    # Prepare daily buckets
    daily_data = {}
    for i in range(7):
        day = (start_date + timedelta(days=i)).isoformat()
        daily_data[day] = {
            "calories": 0,
            "protein_g": 0,
            "fat_g": 0,
            "carbs_g": 0
        }

    # Fill values
    for log in logs:
        log_date = log["created_at"].date().isoformat()

        if log_date in daily_data:
            daily_data[log_date]["calories"] += log["calories"]
            daily_data[log_date]["protein_g"] += log["protein_g"]
            daily_data[log_date]["fat_g"] += log["fat_g"]
            daily_data[log_date]["carbs_g"] += log["carbs_g"]

    # Convert dict → list sorted by date
    result = [
        {
            "date": day,
            "calories": daily_data[day]["calories"],
            "protein_g": daily_data[day]["protein_g"],
            "fat_g": daily_data[day]["fat_g"],
            "carbs_g": daily_data[day]["carbs_g"]
        }
        for day in sorted(daily_data.keys())
    ]

    return {"chart": result}