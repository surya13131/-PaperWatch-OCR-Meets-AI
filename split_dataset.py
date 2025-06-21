import os
import random
import shutil

def split_data(source_dir, train_dir, val_dir, split_ratio=0.8):
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)
    if not os.path.exists(val_dir):
        os.makedirs(val_dir)

    all_files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    if not all_files:
        print(f"⚠️ No files found in {source_dir}")
        return

    random.shuffle(all_files)
    split_point = int(len(all_files) * split_ratio)

    train_files = all_files[:split_point]
    val_files = all_files[split_point:]

    for f in train_files:
        shutil.copy(os.path.join(source_dir, f), os.path.join(train_dir, f))
    for f in val_files:
        shutil.copy(os.path.join(source_dir, f), os.path.join(val_dir, f))

    print(f"✅ {os.path.basename(source_dir)} → {len(train_files)} train | {len(val_files)} val")

# Base path
base_path = "dataset"
categories = ["aadhaar", "rationcard", "fake"]

for category in categories:
    source_folder = os.path.join(base_path, category)
    train_folder = os.path.join(base_path, "train", category)
    
