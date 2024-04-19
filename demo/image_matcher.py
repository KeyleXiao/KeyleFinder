# import cv2

# class ImageMatcher:
#     def __init__(self, big_image_path):
#         self.big_image = cv2.imread(big_image_path)
#         self.big_image_path = big_image_path
    
#     def match(self, single_image_path, show_preview=False):
#         single_image = cv2.imread(single_image_path)
#         result = cv2.matchTemplate(self.big_image, single_image, cv2.TM_CCOEFF_NORMED)
#         min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
#         top_left = max_loc
        
#         if len(single_image.shape) == 2:
#             h, w = single_image.shape
#         else:
#             h, w, _ = single_image.shape
        
#         bottom_right = (top_left[0] + w, top_left[1] + h)
        
#         if show_preview:
#             # 在大图中标记出单独图像的位置
#             marked_image = self.big_image.copy()
#             cv2.rectangle(marked_image, top_left, bottom_right, (0, 255, 0), 2)
#             # 显示标记后的大图
#             cv2.imshow('Located Image', marked_image)
#             cv2.waitKey(0)
#             cv2.destroyAllWindows()
        
#         return top_left, bottom_right