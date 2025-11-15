from fastapi import APIRouter, UploadFile, File
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch, io

predict_router = APIRouter()

model_path = r"C:\Users\ASUS\Desktop\mp_project\custom-food-model-v1"
processor = AutoImageProcessor.from_pretrained(model_path)
model = AutoModelForImageClassification.from_pretrained(model_path)

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

    return {"label": label, "confidence": round(confidence, 3)}
