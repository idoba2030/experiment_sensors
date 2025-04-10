import os

folder_path = 'images'  # or the full path to your images folder
valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}  # add or remove as needed

# 1) List everything in the folder
all_files = os.listdir(folder_path)

# 2) Filter only image files based on extension
image_files = [
    f for f in all_files
    if os.path.splitext(f)[1].lower() in valid_extensions
]

# 3) Sort them if desired
image_files.sort()

print("Found image files:")
for img in image_files:
    print(img)
