import os
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, output_dir="output"):
        self.output_dir = os.path.abspath(output_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.packed_dir = os.path.abspath(os.path.join(self.output_dir, "..", "packed_files"))
        if not os.path.exists(self.packed_dir):
            os.makedirs(self.packed_dir)

    def get_file_list(self):
        file_list = []
        for root, dirs, files in os.walk(self.output_dir):
            for file in files:
                if file != "image_info.txt":
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.output_dir)
                    file_size = os.path.getsize(full_path)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                    file_list.append((rel_path, file_size, mod_time))
        return file_list

    def delete_file(self, file_path):
        if os.path.basename(file_path) == "image_info.txt":
            return False
        if os.path.exists(file_path):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                return True
            except Exception as e:
                logger.error(f"删除文件时发生错误: {e}")
                return False
        return False

    def clear_output_directory(self):
        for root, dirs, files in os.walk(self.output_dir, topdown=False):
            for file in files:
                if file != "image_info.txt":
                    file_path = os.path.join(root, file)
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        logger.error(f"无法删除文件 {file_path}。原因：{e}")
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.rmdir(dir_path)
                except Exception as e:
                    logger.error(f"无法删除目录 {dir_path}。原因：{e}")
        return True

    def get_packed_dir(self):
        return self.packed_dir
