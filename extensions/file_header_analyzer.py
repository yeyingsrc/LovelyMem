import binascii
from magika import Magika
from pathlib import Path

plugin_info = {
    "title": "文件头分析_NEW",
    "description": "分析文件头信息",
    "usage": "选择一个文件,然后点击此插件",
    "category": "文件分析"
}

def run(file_path):
    with open(file_path, 'rb') as f:
        header = f.read(16)

    print("文件头(十六进制):")
    print(binascii.hexlify(header).decode())

    magika = Magika()
    res = magika.identify_path(Path(file_path))
    print(f"识别为: {res.output.ct_label}")

    new_extension = '.' + res.output.ct_label

    new_file_name = Path(file_path).stem + '_fixed' + new_extension
    new_file_path = Path(file_path).parent / new_file_name

    with open(file_path, 'rb') as src_file, open(new_file_path, 'wb') as dest_file:
        dest_file.write(src_file.read())