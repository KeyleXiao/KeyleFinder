@echo off
setlocal

REM 检测 opencv-python 是否已安装
python -c "import cv2; print('opencv-python is installed.')" 2>nul || (
    echo opencv-python is not installed. Installing it now...
    pip install opencv-python
    if %errorlevel% equ 0 (
        echo opencv-python installed successfully!
    ) else (
        echo Failed to install opencv-python.
    )
)

endlocal

python KeyleKitService.py

