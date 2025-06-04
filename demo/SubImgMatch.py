import os
from image_matcher import ImageMatcher

if __name__ == "__main__":
    single_image_path = "/Users/keyle/Documents/ImageFind/single_image.png"
    big_image_path = "/Users/keyle/Documents/ImageFind/big_image.png"
    matcher = ImageMatcher(big_image_path)
    top_left, bottom_right = matcher.match(single_image_path, show_preview=True)
    # print("找到图像在大图中的位置：左上角坐标{}, 右下角坐标{}".format(top_left, bottom_right))
    print("Found image {} in {}, top-left {}, bottom-right {}".format(
        os.path.basename(single_image_path),
        os.path.basename(big_image_path),
        top_left,
        bottom_right,
    ))
