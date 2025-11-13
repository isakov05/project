from transformers import (
    AutoImageProcessor,
    AutoModelForImageClassification,
    TrainingArguments,
    Trainer,
    DefaultDataCollator,
    __version__ as hf_version,
)
from datasets import load_dataset
import torch
from torch import nn
from PIL import Image
import numpy as np
from sklearn.metrics import accuracy_score

# 1) Model & processor
model_name = "nateraw/food"
processor = AutoImageProcessor.from_pretrained(model_name)
model = AutoModelForImageClassification.from_pretrained(model_name)

# 2) Dataset
data_dir = r"C:\Users\ASUS\Desktop\mp_project\Food\pictures"
dataset = load_dataset("imagefolder", data_dir=data_dir, split="train").train_test_split(test_size=0.2)

# 3) Preprocess -> pixel_values tensor, skip bad images
def preprocess(example):
    image = example["image"]
    if isinstance(image, list):
        image = image[0]
    if not isinstance(image, Image.Image):
        example["pixel_values"] = None
        return example
    try:
        image = image.convert("RGB")
        encoding = processor(images=image, return_tensors="pt")
        example["pixel_values"] = encoding["pixel_values"][0]
    except Exception as e:
        print("⚠️ Skipping one image:", e)
        example["pixel_values"] = None
    return example

dataset = dataset.map(preprocess, batched=False)
dataset = dataset.filter(lambda x: x["pixel_values"] is not None)
dataset = dataset.rename_column("label", "labels")
dataset = dataset.remove_columns(["image"])

# 4) Fix classifier head to num_labels
num_labels = len(dataset["train"].features["labels"].names)
print("Number of labels:", num_labels)

# Replace whichever head exists
if hasattr(model, "classifier"):
    in_features = model.classifier.in_features
    model.classifier = nn.Linear(in_features, num_labels)
    print("✅ Replaced model.classifier")
elif hasattr(model, "vit") and hasattr(model.vit, "classifier"):
    in_features = model.vit.classifier.in_features
    model.vit.classifier = nn.Linear(in_features, num_labels)
    print("✅ Replaced model.vit.classifier")
elif hasattr(model, "heads") and hasattr(model.heads, "head"):
    in_features = model.heads.head.in_features
    model.heads.head = nn.Linear(in_features, num_labels)
    print("✅ Replaced model.heads.head")
else:
    raise RuntimeError("❌ Couldn't find classifier layer in model")

# Sync config & model num_labels and label maps
model.config.num_labels = num_labels
model.num_labels = num_labels
model.config.id2label = {i: name for i, name in enumerate(dataset["train"].features["labels"].names)}
model.config.label2id = {v: k for k, v in model.config.id2label.items()}
print(f"✅ Model updated: {num_labels} output labels")
print(f"Config num_labels: {model.config.num_labels}, Model num_labels: {model.num_labels}")

# 5) Metrics
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc}

# 6) Data collator (stacks pixel_values tensors safely)
data_collator = DefaultDataCollator()

# 7) Training arguments with SAFE FALLBACK for older transformers
def make_args():
    base_kwargs = dict(
        output_dir="./custom-food-model-v1",
        learning_rate=5e-5,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        num_train_epochs=5,
        logging_dir="./logs",
        dataloader_pin_memory=False,   # silence pin_memory warning on CPU
        report_to="none",
    )
    try:
        # Try newer API first
        return TrainingArguments(
            evaluation_strategy="epoch",
            save_strategy="epoch",
            logging_strategy="epoch",
            **base_kwargs
        )
    except TypeError:
        # Fallback for older API (no evaluation/save/logging strategies)
        print("ℹ️ Using fallback TrainingArguments (no evaluation_strategy).")
        return TrainingArguments(**base_kwargs)

args = make_args()

# 8) Trainer
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    data_collator=data_collator,
    compute_metrics=compute_metrics if hasattr(args, "evaluation_strategy") else None,
)

# 9) Train & save
trainer.train()
trainer.save_model("./custom-food-model-v1")
processor.save_pretrained("./custom-food-model-v1")
print("✅ Training finished! Model saved as custom-food-model-v1")
