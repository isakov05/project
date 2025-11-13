import os

def get_dir_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):  # avoid broken links
                total += os.path.getsize(fp)
    return total

path = r"C:\Users\ASUS\Desktop\mp_project\custom-food-model-v1"
size_bytes = get_dir_size(path)
print(f"Model size: {size_bytes / (1024*1024):.2f} MB")
