from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from transformers import AutoImageProcessor, AutoModelForImageClassification
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from PIL import Image
import torch, io, os, shutil
from datetime import datetime

from .security import decode_access_token
from .db import foods_collection, food_logs_collection

predict_router = APIRouter()

# -------------------------------
# Load your custom ML model
# -------------------------------
model_path = r"C:\Users\ASUS\Desktop\mp_project\custom-food-model-v1"
processor = AutoImageProcessor.from_pretrained(model_path)
model = AutoModelForImageClassification.from_pretrained(model_path)

# Token reader
auth_scheme = HTTPBearer()


# --------------------------------------------
# Helper: Extract user from JWT
# --------------------------------------------
async def get_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    payload = decode_access_token(token.credentials)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    return payload["user_id"]


# --------------------------------------------
# 1️⃣ Regular prediction
# --------------------------------------------
@predict_router.post("/")
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        pred_id = logits.argmax(-1).item()
        label = model.config.id2label[pred_id]
        probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        confidence = probs[pred_id].item()

    return {
        "label": label,
        "confidence": round(confidence, 3)
    }


# --------------------------------------------
# 2️⃣ AUTO-LOG: upload → predict → log → return
# --------------------------------------------
@predict_router.post("/auto-log")
async def auto_log_food(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user)
):
    # 1️⃣ Save image locally
    upload_dir = "static/uploads/"
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.split(".")[-1]
    saved_name = f"{datetime.utcnow().timestamp()}.{ext}"
    file_path = os.path.join(upload_dir, saved_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"/{file_path}"

    # 2️⃣ Run ML prediction
    image_bytes = open(file_path, "rb").read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        pred_id = outputs.logits.argmax(-1).item()
        predicted_label = model.config.id2label[pred_id]

    predicted_label = predicted_label.lower()

    # 3️⃣ Fetch nutrition from foods database
    food = await foods_collection.find_one({"name": predicted_label})
    if not food:
        raise HTTPException(404, f"Food '{predicted_label}' not found in database")

    # 4️⃣ Prepare nutrition values
    calories = food["nutrition"]["calories"]
    protein = food["nutrition"]["protein_g"]
    fat = food["nutrition"]["fat_g"]
    carbs = food["nutrition"]["carbohydrates_g"]

    # 5️⃣ Log to food_logs
    log = {
        "user_id": user_id,
        "food_id": str(food["_id"]),
        "food_name": predicted_label,
        "calories": calories,
        "protein_g": protein,
        "fat_g": fat,
        "carbs_g": carbs,
        "serving_size": "1 serving",
        "image_url": image_url,
        "created_at": datetime.utcnow()
    }

    result = await food_logs_collection.insert_one(log)

    # 6️⃣ Send response
    return {
        "predicted_food": predicted_label,
        "nutrition": {
            "calories": calories,
            "protein_g": protein,
            "fat_g": fat,
            "carbs_g": carbs
        },
        "image_url": image_url,
        "log_id": str(result.inserted_id)
    }
