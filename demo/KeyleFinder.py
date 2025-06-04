
import os
try:
    import cv2
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError(
        "OpenCV is required for KeyleFinder. Install it with 'pip install opencv-python-headless'."
    ) from exc
import json
import numpy as np


class KeyleFinder:
    def __init__(self, big_image_path):
        self.big_image = cv2.imread(big_image_path)

    @staticmethod
    def _draw_multiline_text(img, text, org, font, scale, color, thickness=1, line_type=cv2.LINE_AA):
        """Draw text that automatically wraps when exceeding image width."""
        if text is None:
            return
        x, y = org
        max_width = img.shape[1] - x - 10

        current = ""
        lines = []
        for ch in text:
            if ch == "\n":
                lines.append(current)
                current = ""
                continue
            size = cv2.getTextSize(current + ch, font, scale, thickness)[0][0]
            if size > max_width and current:
                lines.append(current)
                current = ch
            else:
                current += ch
        if current:
            lines.append(current)

        line_height = cv2.getTextSize("A", font, scale, thickness)[0][1] + 5
        for idx, ln in enumerate(lines):
            cv2.putText(img, ln, (x, y + idx * line_height), font, scale, color, thickness, line_type)

    def _show_preview(self, single_image=None, dst_points=None, angle=None, scale=None, label=None, transform=None, found=True):
        """Preview the match by overlaying ``single_image`` on ``self.big_image``.

        ``dst_points`` should contain the four corner points of the matched
        region in clockwise order. ``angle`` and ``scale`` are kept for backward
        compatibility but the overlay is generated using an affine
        transformation (rotation + uniform scale) so that the overlay is not
        distorted by perspective. When ``found`` is False, only ``label`` is
        drawn on the big image to indicate the match was not successful.
        """

        preview = self.big_image.copy()

        if found and dst_points is not None and single_image is not None:
            # outline of matched area
            cv2.polylines(preview, [np.int32(dst_points)], True, (0, 255, 0), 2)

            h, w = single_image.shape[:2]

            if transform is None:
                if angle is None:
                    dx = dst_points[1][0] - dst_points[0][0]
                    dy = dst_points[1][1] - dst_points[0][1]
                    angle = np.degrees(np.arctan2(dy, dx))

                if scale is None:
                    dst_w = np.linalg.norm(dst_points[1] - dst_points[0])
                    dst_h = np.linalg.norm(dst_points[3] - dst_points[0])
                    scale_x = dst_w / w
                    scale_y = dst_h / h
                    scale = (scale_x + scale_y) / 2.0

                dst_center = tuple(np.mean(dst_points, axis=0))
                transform = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
                transform[0, 2] += dst_center[0] - w / 2
                transform[1, 2] += dst_center[1] - h / 2

            overlay = cv2.warpAffine(
                single_image, transform, (self.big_image.shape[1], self.big_image.shape[0])
            )

            gray = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
            inv_mask = cv2.bitwise_not(mask)

            bg = cv2.bitwise_and(preview, preview, mask=inv_mask)
            fg = cv2.bitwise_and(overlay, overlay, mask=mask)
            preview = cv2.add(bg, fg)

            center = tuple(np.mean(dst_points, axis=0).astype(int))
            cv2.drawMarker(preview, center, (255, 0, 0), cv2.MARKER_CROSS, 20, 2)

            if label is not None:
                x = int(np.min(dst_points[:, 0]))
                y = int(np.min(dst_points[:, 1])) - 10
                y = max(y, 0)
                self._draw_multiline_text(
                    preview,
                    label,
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    1,
                )
        else:
            text = "未成功匹配" if label is None else f"未成功匹配: {label}"
            self._draw_multiline_text(
                preview,
                text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        cv2.imshow('Located Image', preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def match_feature(self, single_image_path, show_preview=True):
        """Match image using ORB feature detection, allowing partial occlusion.
        Returns the bounding box of the matched area and the rotation angle
        (in degrees) of the found image relative to its original orientation.
        """
        single_image = cv2.imread(single_image_path)
        if single_image is None or self.big_image is None:
            if show_preview:
                self._show_preview(label=single_image_path, found=False)
            return None, None, None, None

        single_gray = cv2.cvtColor(single_image, cv2.COLOR_BGR2GRAY)
        big_gray = cv2.cvtColor(self.big_image, cv2.COLOR_BGR2GRAY)

        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(single_gray, None)
        kp2, des2 = orb.detectAndCompute(big_gray, None)
        if des1 is None or des2 is None:
            if show_preview:
                self._show_preview(label=single_image_path, found=False)
            return None, None, None, None

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(des1, des2, k=2)

        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append(m)

        if len(good) < 4:
            if show_preview:
                self._show_preview(label=single_image_path, found=False)
            return None, None, None, None

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good])
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good])

        # 使用 estimateAffinePartial2D 计算只包含旋转、平移和等比例缩放的变换，
        # 避免得到带有透视和梯形拉伸的 homography
        M, mask = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC)
        if M is None:
            if show_preview:
                self._show_preview(label=single_image_path, found=False)
            return None, None, None, None

        h, w = single_gray.shape
        pts = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
        dst = cv2.transform(pts[None, :, :], M)[0]

        x_coords = dst[:, 0]
        y_coords = dst[:, 1]
        top_left = (int(min(x_coords)), int(min(y_coords)))
        bottom_right = (int(max(x_coords)), int(max(y_coords)))

        # calculate rotation angle using the vector from the first point to the last
        # 取上边缘的两个点计算旋转角度
        # 从估算得到的仿射矩阵中提取旋转角度和缩放比例
        angle = np.degrees(np.arctan2(M[1, 0], M[0, 0]))
        scale = float(np.sqrt(M[0, 0] ** 2 + M[1, 0] ** 2))

        if show_preview:
            self._show_preview(
                single_image,
                dst.reshape(4, 2),
                angle,
                scale,
                label=single_image_path,
                transform=M,
            )

        return top_left, bottom_right, float(angle), scale
    
    def match(self, single_image_path, mode=cv2.TM_CCOEFF_NORMED, show_preview=True):
        single_image = cv2.imread(single_image_path)
        if single_image is None or self.big_image is None:
            if show_preview:
                self._show_preview(label=single_image_path, found=False)
            return None, None, None

        result = cv2.matchTemplate(self.big_image, single_image, mode)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 如果最大匹配值小于阈值，则认为没有找到匹配的位置
        threshold = 0.8  # 设置阈值
        if max_val < threshold:
            if show_preview:
                self._show_preview(label=single_image_path, found=False)
            return None, None, None
        
        top_left = max_loc
        
        if len(single_image.shape) == 2:
            h, w = single_image.shape
        else:
            h, w, _ = single_image.shape
        
        bottom_right = (top_left[0] + w, top_left[1] + h)
        
        if show_preview:
            dst = np.float32([
                [top_left[0], top_left[1]],
                [top_left[0] + w - 1, top_left[1]],
                [top_left[0] + w - 1, top_left[1] + h - 1],
                [top_left[0], top_left[1] + h - 1]
            ])
            translation = np.float32([
                [1, 0, top_left[0]],
                [0, 1, top_left[1]],
            ])
            self._show_preview(
                single_image,
                dst,
                0.0,
                1.0,
                label=single_image_path,
                transform=translation,
            )
        
        return top_left, bottom_right, 0.0

def find_layer_images(directory=os.getcwd(), layer_filename="layer.png"):
    layer_images = []
    other_images = []
    for file in os.listdir(directory):
        if file == layer_filename:
            layer_images.append(os.path.join(directory, file))
        elif file.lower().endswith((".png", ".jpg")):
            other_images.append(os.path.join(directory, file))
    return layer_images, other_images

def match_images(layer_image, other_images, mode=cv2.TM_CCOEFF_NORMED, show_preview=True):
    finder = KeyleFinder(layer_image)
    matches = {}
    for other_image in other_images:
        top_left, bottom_right, angle = finder.match(other_image, mode, show_preview)
        if top_left is not None and bottom_right is not None:
            matches[os.path.basename(other_image)] = {
                "top_left": {"x": top_left[0], "y": top_left[1]},
                "bottom_right": {"x": bottom_right[0], "y": bottom_right[1]},
                "angle": angle,
                "scale": 1.0
            }
    return matches

def match_images_with_order(layer_image, other_images, show_preview=True):
    """Match images allowing occlusion and calculate layering order.
    The rotation angle of each match is also recorded.
    """
    finder = KeyleFinder(layer_image)
    matches = {}
    path_map = {}
    for other_image in other_images:
        top_left, bottom_right, angle, scale = finder.match_feature(other_image, show_preview)
        if top_left is not None and bottom_right is not None:
            name = os.path.basename(other_image)
            path_map[name] = other_image
            matches[name] = {
                "top_left": {"x": top_left[0], "y": top_left[1]},
                "bottom_right": {"x": bottom_right[0], "y": bottom_right[1]},
                "angle": angle,
                "scale": scale
            }

    order = determine_layer_order(finder.big_image, matches, path_map)
    return matches, order

def determine_layer_order(big_image, matches, path_map):
    """Determine front/back order based on overlap."""
    names = list(matches.keys())
    levels = {name: 0 for name in names}

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            top = compare_overlap(big_image, matches[n1], path_map[n1], matches[n2], path_map[n2])
            if top == n1:
                levels[n1] = max(levels[n1], levels[n2] + 1)
            elif top == n2:
                levels[n2] = max(levels[n2], levels[n1] + 1)

    ordered = sorted(names, key=lambda n: levels[n])
    return ordered

def compare_overlap(big_image, box1, path1, box2, path2):
    x1 = max(box1["top_left"]["x"], box2["top_left"]["x"])
    y1 = max(box1["top_left"]["y"], box2["top_left"]["y"])
    x2 = min(box1["bottom_right"]["x"], box2["bottom_right"]["x"])
    y2 = min(box1["bottom_right"]["y"], box2["bottom_right"]["y"])
    if x1 >= x2 or y1 >= y2:
        return None

    big_patch = big_image[y1:y2, x1:x2]
    if big_patch.size == 0:
        return None

    img1 = cv2.imread(path1)
    img2 = cv2.imread(path2)

    p1 = img1[y1 - box1["top_left"]["y"]:y2 - box1["top_left"]["y"], x1 - box1["top_left"]["x"]:x2 - box1["top_left"]["x"]]
    p2 = img2[y1 - box2["top_left"]["y"]:y2 - box2["top_left"]["y"], x1 - box2["top_left"]["x"]:x2 - box2["top_left"]["x"]]

    if p1.size == 0 or p2.size == 0:
        return None

    g_big = cv2.cvtColor(big_patch, cv2.COLOR_BGR2GRAY)
    g1 = cv2.cvtColor(p1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(p2, cv2.COLOR_BGR2GRAY)

    diff1 = np.sum(np.abs(g_big.astype("float") - g1.astype("float")))
    diff2 = np.sum(np.abs(g_big.astype("float") - g2.astype("float")))

    if diff1 < diff2:
        return os.path.basename(path1)
    elif diff2 < diff1:
        return os.path.basename(path2)
    else:
        return None

def save_matches(matches, output_file):
    with open(output_file, 'w') as f:
        json.dump(matches, f, indent=4)

def process_directory(directory=os.getcwd(), recursive=True, show_preview=True, use_feature=False):
    layer_images, other_images = find_layer_images(directory)
    other_images.sort(key=lambda x: get_image_size(x), reverse=True)

    for layer_image in layer_images:
        output_file = os.path.join(os.path.dirname(layer_image), "layer.txt")
        if os.path.exists(output_file):
            os.remove(output_file)

        if use_feature:
            matches, order = match_images_with_order(layer_image, other_images, show_preview)
            result = {"matches": matches, "order": order}
        else:
            matches = match_images(layer_image, other_images, cv2.TM_CCOEFF_NORMED, show_preview)
            result = matches

        save_matches(result, output_file)
    
    if recursive:
        for root, dirs, _ in os.walk(directory):
            for dir_name in dirs:
                process_directory(os.path.join(root, dir_name), recursive=True, show_preview=show_preview, use_feature=use_feature)

def get_image_size(image_path):
    img = cv2.imread(image_path)
    if img is not None:
        return img.shape[0] * img.shape[1]
    else:
        return 0

# 示例用法
if __name__ == "__main__":
    # 使用 ORB 特征匹配并计算图层顺序，结果将包含每个切片在大图中的旋转角度
    process_directory(show_preview=True, use_feature=True)
