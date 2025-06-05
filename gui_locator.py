import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import tempfile
import os
import pyautogui
import keyboard
import time

from KeyleFinderModule import KeyleFinderModule

HOTKEY = 'F2'  # Default hotkey
HOTKEY_OPTIONS = [f'F{i}' for i in range(1, 13)]


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
        self.geometry('240x320')
        self.resizable(False, False)

        ttk.Style(self).theme_use('clam')

        self.sub_img_path = None
        self.debug_var = tk.BooleanVar(value=False)
        self.auto_start_var = tk.BooleanVar(value=False)
        self.hotkey_var = tk.StringVar(value=HOTKEY)

        top = ttk.Frame(self)
        top.pack(fill='x', pady=5)

        load_btn = ttk.Button(top, text='📂', width=3, command=self.load_image)
        load_btn.pack(side='left', padx=2)

        start_btn = ttk.Button(top, text='▶', width=3, command=self.trigger_search)
        start_btn.pack(side='left', padx=2)

        setting_btn = ttk.Button(top, text='⚙', width=3, command=self.open_settings)
        setting_btn.pack(side='left', padx=2)

        about_btn = ttk.Button(top, text='About', command=self.show_about)
        about_btn.pack(side='right', padx=5)

        self.photo_label = ttk.Label(self, text='No Image', relief='groove')
        self.photo_label.pack(padx=10, pady=5, fill='both', expand=True)

        self.info_label = ttk.Label(
            self,
            text='Locate a captured image on your screen.\nPress start or the hotkey to begin.',
            font=('Arial', 9),
        )
        self.info_label.pack(side='bottom', pady=5)

        self.hotkey_var.trace_add('write', self.update_hotkey)
        keyboard.add_hotkey(self.hotkey_var.get(), self.trigger_search)
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
        if self.auto_start_var.get():
            self.trigger_search()

    def update_hotkey(self, *_):
        keyboard.clear_all_hotkeys()
        keyboard.add_hotkey(self.hotkey_var.get(), self.trigger_search)

    def show_about(self):
        messagebox.showinfo('About', 'KeyleFinder\nAuthor: keyle\nhttps://vrast.cn')

    def open_settings(self):
        win = tk.Toplevel(self)
        win.title('Settings')
        win.resizable(False, False)
        ttk.Checkbutton(win, text='Debug', variable=self.debug_var).pack(anchor='w', padx=10, pady=5)
        ttk.Checkbutton(win, text='Auto Start', variable=self.auto_start_var).pack(anchor='w', padx=10, pady=5)
        ttk.Label(win, text='Hotkey:').pack(anchor='w', padx=10, pady=(10, 0))
        ttk.Combobox(win, width=4, state='readonly',
                     values=HOTKEY_OPTIONS, textvariable=self.hotkey_var).pack(anchor='w', padx=10, pady=5)
        ttk.Button(win, text='Close', command=win.destroy).pack(pady=10)

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
            result = finder.locate(self.sub_img_path, debug=self.debug_var.get())
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
