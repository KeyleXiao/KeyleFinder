import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import tempfile
import os
import pyautogui
import keyboard

from KeyleFinderModule import KeyleFinderModule

HOTKEY = 'F1'  # Configurable hotkey

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Image Locator')
        self.geometry('200x230')
        self.resizable(False, False)
        self.sub_img_path = None
        self.photo_label = tk.Label(self, text='No Image')
        self.photo_label.place(x=0, y=30, width=200, height=200)
        load_btn = tk.Button(self, text='Load Image', command=self.load_image)
        load_btn.place(x=40, y=0, width=120, height=25)
        keyboard.add_hotkey(HOTKEY, self.trigger_search)
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[('Image Files', '*.png *.jpg *.jpeg *.bmp')])
        if not path:
            return
        self.sub_img_path = path
        img = Image.open(path)
        img.thumbnail((200, 200))
        self.tk_img = ImageTk.PhotoImage(img)
        self.photo_label.config(image=self.tk_img, text='')

    def trigger_search(self):
        if not self.sub_img_path:
            messagebox.showwarning('Warning', 'Load sub image first')
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            screenshot = pyautogui.screenshot()
            screenshot.save(tmp.name)
            finder = KeyleFinderModule(tmp.name)
            result = finder.locate(self.sub_img_path, debug=True)
        os.unlink(tmp.name)
        if result.get('status') == 0:
            tl = result['top_left']
            br = result['bottom_right']
            center_x = (tl[0] + br[0]) // 2
            center_y = (tl[1] + br[1]) // 2
            pyautogui.moveTo(center_x, center_y)
        else:
            messagebox.showinfo('Result', 'Match failed')

    def on_close(self):
        keyboard.clear_all_hotkeys()
        self.destroy()

if __name__ == '__main__':
    App().mainloop()
