import os
import cv2
import json


class KeyleFinder:
    def __init__(self, big_image_path):
        self.big_image = cv2.imread(big_image_path)
    
    def match(self, single_image_path, mode=cv2.TM_CCOEFF_NORMED, show_preview=False):
        single_image = cv2.imread(single_image_path)
        result = cv2.matchTemplate(self.big_image, single_image, mode)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 如果最大匹配值小于阈值，则认为没有找到匹配的位置
        threshold = 0.8  # 设置阈值
        if max_val < threshold:
            return None, None
        
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
    for file in os.listdir(directory):
        if file == layer_filename:
            layer_images.append(os.path.join(directory, file))
        elif file.lower().endswith((".png", ".jpg")):
            other_images.append(os.path.join(directory, file))
    return layer_images, other_images

def match_images(layer_image, other_images, mode=cv2.TM_CCOEFF_NORMED, show_preview=False):
    finder = KeyleFinder(layer_image)
    matches = {}
    for other_image in other_images:
        top_left, bottom_right = finder.match(other_image, mode, show_preview)
        if top_left is not None and bottom_right is not None:
            matches[os.path.basename(other_image)] = {
                "top_left": {"x": top_left[0], "y": top_left[1]},
                "bottom_right": {"x": bottom_right[0], "y": bottom_right[1]}
            }
    return matches

def save_matches(matches, output_file):
    with open(output_file, 'w') as f:
        json.dump(matches, f, indent=4)

def process_directory(directory=os.getcwd(), recursive=True, show_preview=False):
    layer_images, other_images = find_layer_images(directory)
    # 对其他图片按照像素尺寸进行排序
    other_images.sort(key=lambda x: get_image_size(x), reverse=True)
    # 默认模式: TM_CCOEFF_NORMED
    for layer_image in layer_images:
        output_file = os.path.join(os.path.dirname(layer_image), "layer.txt")
        # 删除之前的同名文件
        if os.path.exists(output_file):
            os.remove(output_file)
        matches = match_images(layer_image, other_images, cv2.TM_CCOEFF_NORMED, show_preview)
        save_matches(matches, output_file)
    
    if recursive:
        for root, dirs, _ in os.walk(directory):
            for dir_name in dirs:
                process_directory(os.path.join(root, dir_name), recursive=True, show_preview=show_preview)

def get_image_size(image_path):
    img = cv2.imread(image_path)
    if img is not None:
        return img.shape[0] * img.shape[1]
    else:
        return 0

# 示例用法
if __name__ == "__main__":
    process_directory(show_preview=False)
