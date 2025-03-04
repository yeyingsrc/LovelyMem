import os
import hashlib
import json

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def generate_update_json(directory, output_json, exclude_dirs=None, exclude_files=None):
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_files is None:
        exclude_files = []

    exclude_dirs = set(os.path.abspath(os.path.join(directory, d)) for d in exclude_dirs)
    exclude_files = set(os.path.abspath(os.path.join(directory, f)) for f in exclude_files)

    update_list = []

    for root, dirs, files in os.walk(directory):
        # 排除指定的目录
        dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in exclude_dirs]

        for file in files:
            file_path = os.path.join(root, file)
            if os.path.abspath(file_path) not in exclude_files:
                file_md5 = calculate_md5(file_path)
                relative_path = os.path.relpath(file_path, directory)
                update_list.append({"file": relative_path, "md5": file_md5})

    with open(output_json, 'w') as json_file:
        json.dump(update_list, json_file, indent=4)

# 使用方法
directory_to_scan = '.'
output_json_file = 'update_list.json'
exclude_directories = ['Tools', 'python', 'Archive', 'output', '__pycache__', 'pyarmor_runtime_000000', 'bak']
exclude_files = ['license', 'OfflineLicense', 'CteateUpdateJson.py', 'Update.py', 'update_list.json']
generate_update_json(directory_to_scan, output_json_file, exclude_directories, exclude_files)
