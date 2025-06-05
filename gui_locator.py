import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import tempfile
import os
import pyautogui
import keyboard
import time

from KeyleFinderModule import KeyleFinderModule

HOTKEY = 'F2'  # Configurable hotkey


class ScreenCropper(tk.Toplevel):
    def __init__(self, master, screenshot, callback):
        super().__init__(master)
        self.callback = callback
        self.screenshot = screenshot
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.overrideredirect(True)
        self.canvas = tk.Canvas(self, cursor='cross')
        self.canvas.pack(fill='both', expand=True)
        self.tk_img = ImageTk.PhotoImage(screenshot)
        self.canvas.create_image(0, 0, image=self.tk_img, anchor='nw')
        self.rect = None
        self.start_x = 0
        self.start_y = 0
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )

    def on_drag(self, event):
        if not self.rect:
            return
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if not self.rect:
            self.destroy()
            self.callback(None)
            return
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        if x2 - x1 < 1 or y2 - y1 < 1:
            self.destroy()
            self.callback(None)
            return
        cropped = self.screenshot.crop((x1, y1, x2, y2))
        self.destroy()
        self.callback(cropped)


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
        # Minimize to taskbar instead of fully hiding so the user can
        # restore the window manually if needed.
        self.iconify()
        time.sleep(0.2)
        screenshot = pyautogui.screenshot()
        ScreenCropper(self, screenshot, self.on_crop_done)

    def on_crop_done(self, cropped):
        self.deiconify()
        if cropped is None:
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            cropped.save(tmp.name)
            self.sub_img_path = tmp.name
        img = cropped.copy()
        img.thumbnail((200, 200))
        self.tk_img = ImageTk.PhotoImage(img)
        self.photo_label.config(image=self.tk_img, text='')

    def trigger_search(self):
        if not self.sub_img_path:
            messagebox.showwarning('Warning', 'Load sub image first')
            return
        self.iconify()
        self.update()
        time.sleep(0.2)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            screenshot = pyautogui.screenshot()
            screenshot.save(tmp.name)
            finder = KeyleFinderModule(tmp.name)
            result = finder.locate(self.sub_img_path, debug=True)
        os.unlink(tmp.name)
        # Keep the window minimized after locating so the user can
        # continue working without interruption.
        if result.get('status') == 0:
            tl = result['top_left']
            br = result['bottom_right']
            center_x = (tl[0] + br[0]) // 2
            center_y = (tl[1] + br[1]) // 2
            pyautogui.moveTo(center_x, center_y)
            # Perform a single left click at the located position
            pyautogui.click()
        else:
            messagebox.showinfo('Result', 'Match failed')

    def on_close(self):
        keyboard.clear_all_hotkeys()
        self.destroy()


if __name__ == '__main__':
    App().mainloop()
