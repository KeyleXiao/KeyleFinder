import os
import cv2
import json
import getpass  
from datetime import datetime

class KeyleFinder:
    def __init__(self, big_image_path):
        self.big_image = cv2.imread(big_image_path)
        self.big_image_path = big_image_path
    
    def match(self, single_image_path, mode=cv2.TM_CCOEFF_NORMED, show_preview=False):
        single_image = cv2.imread(single_image_path)
        result = cv2.matchTemplate(self.big_image, single_image, mode)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        top_left = max_loc
        
        if len(single_image.shape) == 2:
            h, w = single_image.shape
        else:
            h, w, _ = single_image.shape
        
        bottom_right = (top_left[0] + w, top_left[1] + h)
        
        if show_preview:
            # 在大图中标记出单独图像的位置
            marked_image = self.big_image.copy()
            cv2.rectangle(marked_image, top_left, bottom_right, (0, 255, 0), 2)
            # 显示标记后的大图
            cv2.imshow('Located Image', marked_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        return top_left, bottom_right

def find_layer_images(directory=os.getcwd(), layer_filename="layer.png"):
    layer_images = []
    other_images = []
    for root, _, files in os.walk(directory):
        if layer_filename in files:
            layer_images.append(os.path.join(root, layer_filename))
        for file in files:
            if file.endswith(".png") and file != layer_filename:
                other_images.append(os.path.join(root, file))
    return layer_images, other_images

def match_images(layer_image, other_images, mode=cv2.TM_CCOEFF_NORMED, show_preview=False):
    finder = KeyleFinder(layer_image)
    matches = {}
    for other_image in other_images:
        top_left, bottom_right = finder.match(other_image, mode, show_preview)
        matches[os.path.basename(other_image)] = {
            "top_left": {"x": top_left[0], "y": top_left[1]},
            "bottom_right": {"x": bottom_right[0], "y": bottom_right[1]}
        }
    return matches

def save_matches(matches, output_file, file_info=None):
    with open(output_file, 'w') as f:
        # 写入文件信息
        if file_info:
            f.write(f"{file_info}\n\n")
        json.dump(matches, f, indent=4)

def process_directory(directory=os.getcwd(), recursive=True, file_info=None):
    layer_images, other_images = find_layer_images(directory)
    for layer_image in layer_images:
        output_file = os.path.join(os.path.dirname(layer_image), "layer.txt")
        # 删除之前的同名文件
        if os.path.exists(output_file):
            os.remove(output_file)
        # 默认模式: TM_CCOEFF_NORMED
        matches = match_images(layer_image, other_images, cv2.TM_CCOEFF_NORMED, show_preview=False)
        save_matches(matches, output_file, file_info)
        # 其他模式示例
        # matches = match_images(layer_image, other_images, cv2.TM_CCOEFF_NORMED, show_preview=True)
        # save_matches(matches, os.path.join(os.path.dirname(layer_image), "layer_TM_CCOEFF_NORMED.txt"))
        # matches = match_images(layer_image, other_images, cv2.TM_CCOEFF, show_preview=True)
        # save_matches(matches, os.path.join(os.path.dirname(layer_image), "layer_TM_CCOEFF.txt"))
        # matches = match_images(layer_image, other_images, cv2.TM_CCORR_NORMED, show_preview=True)
        # save_matches(matches, os.path.join(os.path.dirname(layer_image), "layer_TM_CCORR_NORMED.txt"))
    
    if recursive:
        for root, dirs, _ in os.walk(directory):
            for dir_name in dirs:
                process_directory(os.path.join(root, dir_name), recursive=True)

# 示例用法
if __name__ == "__main__":
    directory = os.getcwd()
    # directory = "/path/to/your/directory"
    # 获取当前系统时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 构建文件信息字符串
    file_info = f"Version: 1.0 Author: keyle Update: {current_time}"
    process_directory(directory, file_info=file_info)