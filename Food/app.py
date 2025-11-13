from fastapi import FastAPI, File, UploadFile
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import io

# === Load model and processor ===
model_path = r"C:\Users\ASUS\Desktop\mp_project\custom-food-model-v1"
processor = AutoImageProcessor.from_pretrained(model_path)
model = AutoModelForImageClassification.from_pretrained(model_path)

app = FastAPI(title="Food Classification API")

# === Predict endpoint ===
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Read image from upload
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Preprocess and predict
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        pred_id = logits.argmax(-1).item()
        label = model.config.id2label[pred_id]
        probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        confidence = probs[pred_id].item()
    return {"predicted_label": label, "confidence": round(confidence, 3)}


# === Run ===
# Run this in terminal: uvicorn app:app --reload
