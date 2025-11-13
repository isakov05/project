from datasets import load_dataset

data_dir = r"C:\Users\ASUS\Desktop\mp_project\Food\images"
dataset = load_dataset("imagefolder", data_dir=data_dir, split="train")

print("✅ Sample entries:")
print(dataset[0])   # print the first item
print("🧾 Total samples:", len(dataset))
