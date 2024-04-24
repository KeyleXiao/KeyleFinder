#!/bin/bash

# 检测 opencv-python 是否已安装
if ! python -c "import cv2; print(cv2.__version__)"; then
    echo "opencv-python is not installed. Installing it now..."
    pip install opencv-python
    echo "opencv-python installed successfully!"
else
    echo "opencv-python is already installed."
fi

python python KeyleKitService.py