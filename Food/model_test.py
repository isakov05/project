from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import torch.nn.functional as F

# Load your fine-tuned model
model_path = "./custom-food-model-v1"
processor = AutoImageProcessor.from_pretrained(model_path)
model = AutoModelForImageClassification.from_pretrained(model_path)

# Path to your test image
image_path = r"C:\Users\ASUS\Desktop\mp_project\Food\test_images\burger.jpg"

# Preprocess
image = Image.open(image_path).convert("RGB")
inputs = processor(images=image, return_tensors="pt")

# Predict
with torch.no_grad():
    outputs = model(**inputs)
    probs = F.softmax(outputs.logits, dim=-1)[0]
    top_idx = torch.argmax(probs).item()

# Display result
pred_label = model.config.id2label[top_idx]
print(f"Prediction: {pred_label} ({probs[top_idx]:.4f})")
