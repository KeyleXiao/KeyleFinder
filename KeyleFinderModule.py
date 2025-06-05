import json
try:
    import cv2
except ImportError as exc:
    raise ImportError(
        "OpenCV is required for KeyleFinderModule. Install it with 'pip install opencv-python-headless'."
    ) from exc
import numpy as np


class KeyleFinderModule:
    """Locate a sub-image within a big image using ORB feature matching."""

    def __init__(self, big_image_path: str):
        self.big_image = cv2.imread(big_image_path)

    @staticmethod
    def _draw_multiline_text(img, text, org, font, scale, color, thickness=1, line_type=cv2.LINE_AA):
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
        preview = self.big_image.copy()

        if found and dst_points is not None and single_image is not None:
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
            overlay = cv2.warpAffine(single_image, transform, (self.big_image.shape[1], self.big_image.shape[0]))
            gray = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
            inv_mask = cv2.bitwise_not(mask)
            bg = cv2.bitwise_and(preview, preview, mask=inv_mask)
            fg = cv2.bitwise_and(overlay, overlay, mask=mask)
            preview = cv2.add(bg, fg)
            center = tuple(np.mean(dst_points, axis=0).astype(int))
            cv2.drawMarker(preview, center, (255, 0, 0), cv2.MARKER_CROSS, 20, 2)
            if label is not None:
                self._draw_multiline_text(preview, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        else:
            text = "Match failed" if label is None else label
            self._draw_multiline_text(preview, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow('Located Image', preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def _match_feature(self, single_image_path):
        single_image = cv2.imread(single_image_path)
        if single_image is None or self.big_image is None:
            return None
        single_gray = cv2.cvtColor(single_image, cv2.COLOR_BGR2GRAY)
        big_gray = cv2.cvtColor(self.big_image, cv2.COLOR_BGR2GRAY)
        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(single_gray, None)
        kp2, des2 = orb.detectAndCompute(big_gray, None)
        if des1 is None or des2 is None:
            return None
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(des1, des2, k=2)
        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append(m)
        if len(good) < 4:
            return None
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good])
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good])
        M, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC)
        if M is None:
            return None
        h, w = single_gray.shape
        pts = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
        dst = cv2.transform(pts[None, :, :], M)[0]
        x_coords = dst[:, 0]
        y_coords = dst[:, 1]
        top_left = (int(min(x_coords)), int(min(y_coords)))
        bottom_right = (int(max(x_coords)), int(max(y_coords)))
        angle = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
        scale = float(np.sqrt(M[0, 0] ** 2 + M[1, 0] ** 2))
        return top_left, bottom_right, angle, scale, single_image, dst.reshape(4, 2), M

    def _match_template(self, single_image_path, threshold: float = 0.8):
        """Fallback template matching when feature matching fails."""
        single_image = cv2.imread(single_image_path)
        if single_image is None or self.big_image is None:
            return None
        result = cv2.matchTemplate(self.big_image, single_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val < threshold:
            return None
        h, w = single_image.shape[:2]
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        dst = np.float32([
            [top_left[0], top_left[1]],
            [top_left[0] + w - 1, top_left[1]],
            [top_left[0] + w - 1, top_left[1] + h - 1],
            [top_left[0], top_left[1] + h - 1],
        ])
        transform = np.float32([[1, 0, top_left[0]], [0, 1, top_left[1]]])
        return top_left, bottom_right, 0.0, 1.0, single_image, dst, transform

    def locate(self, sub_image_path: str, debug: bool = False):
        match = self._match_feature(sub_image_path)
        if match is None:
            match = self._match_template(sub_image_path)
            if match is None:
                result = {"status": 1}
                if debug:
                    self._show_preview(label=json.dumps(result, ensure_ascii=False), found=False)
                return result

        top_left, bottom_right, angle, scale, img, pts, M = match
        result = {
            "status": 0,
            "top_left": [top_left[0], top_left[1]],
            "bottom_right": [bottom_right[0], bottom_right[1]],
            "scale": scale,
        }
        if debug:
            self._show_preview(img, pts, angle, scale, label=json.dumps(result, ensure_ascii=False), transform=M, found=True)
        return result
