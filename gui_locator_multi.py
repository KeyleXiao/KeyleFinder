import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import tempfile
import os
import json
import base64
import pyautogui
import keyboard
import time

from KeyleFinderModule import KeyleFinderModule

HOTKEY = 'F2'
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
        self.title('Multi Locator')
        self.geometry('360x360')
        self.resizable(False, False)

        ttk.Style(self).theme_use('clam')

        self.items = []  # each item is {'path': path, 'double_click': False}
        self.debug_var = tk.BooleanVar(value=False)
        self.auto_start_var = tk.BooleanVar(value=False)
        self.loop_var = tk.BooleanVar(value=False)
        self.hotkey_var = tk.StringVar(value=HOTKEY)

        top = ttk.Frame(self)
        top.pack(fill='x', pady=5)

        add_btn = ttk.Button(top, text='➕', width=3, command=self.add_item)
        add_btn.pack(side='left', padx=2)

        start_btn = ttk.Button(top, text='▶', width=3, command=self.trigger_search)
        start_btn.pack(side='left', padx=2)

        export_btn = ttk.Button(top, text='💾', width=3, command=self.export_items)
        export_btn.pack(side='left', padx=2)

        import_btn = ttk.Button(top, text='📥', width=3, command=self.import_items)
        import_btn.pack(side='left', padx=2)

        setting_btn = ttk.Button(top, text='⚙', width=3, command=self.open_settings)
        setting_btn.pack(side='left', padx=2)

        about_btn = ttk.Button(top, text='About', command=self.show_about)
        about_btn.pack(side='right', padx=5)

        self.tree = ttk.Treeview(
            self,
            columns=('click',),
            show='tree headings',
            height=8,
        )
        self.tree.heading('#0', text='名称')
        self.tree.column('#0', width=200)
        self.tree.heading('click', text='点击')
        self.tree.column('click', width=60, anchor='center')
        self.tree.pack(padx=10, pady=5, fill='x')
        self.tree.bind('<Double-1>', self.on_tree_double_click)

        self.photo_label = ttk.Label(self, text='No Image', relief='groove')
        self.photo_label.pack(padx=10, pady=5, fill='both', expand=True)

        self.log_label = ttk.Label(self, text='', foreground='gray')
        self.log_label.pack(side='bottom', fill='x')
        self.log_label.bind('<Button-1>', self.copy_log)

        self.hotkey_var.trace_add('write', self.update_hotkey)
        keyboard.add_hotkey(self.hotkey_var.get(), self.trigger_search)
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def log(self, msg):
        self.log_label.config(text=msg)

    def copy_log(self, _):
        self.clipboard_clear()
        self.clipboard_append(self.log_label.cget('text'))

    def on_tree_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id or column != '#1':
            return
        idx = self.tree.index(item_id)
        item = self.items[idx]
        item['double_click'] = not item.get('double_click', False)
        self.tree.set(item_id, 'click', '双击' if item['double_click'] else '单击')

    def add_item(self):
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
            path = tmp.name
        img = cropped.copy()
        img.thumbnail((200, 200))
        tk_img = ImageTk.PhotoImage(img)
        self.photo_label.config(image=tk_img, text='')
        self.photo_label.image = tk_img
        self.items.append({'path': path, 'double_click': False})
        self.tree.insert('', 'end', text=os.path.basename(path), values=('单击',))
        if self.auto_start_var.get():
            self.trigger_search()

    def export_items(self):
        if not self.items:
            messagebox.showinfo('Info', 'No items to export')
            return
        file = filedialog.asksaveasfilename(defaultextension='.json')
        if not file:
            return
        data = []
        for item in self.items:
            with open(item['path'], 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            data.append({'image': encoded, 'double_click': item.get('double_click', False)})
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        self.log(f'Exported {len(self.items)} items to {file}')

    def import_items(self):
        file = filedialog.askopenfilename(filetypes=[('JSON', '*.json')])
        if not file:
            return
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for entry in data:
            img_data = base64.b64decode(entry['image'])
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(img_data)
                path = tmp.name
            dbl = entry.get('double_click', False)
            self.items.append({'path': path, 'double_click': dbl})
            txt = '双击' if dbl else '单击'
            self.tree.insert('', 'end', text=os.path.basename(path), values=(txt,))
        self.log(f'Imported {len(data)} items from {file}')

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
        loop_chk = ttk.Checkbutton(win, text='循环执行 (危险)', variable=self.loop_var)
        loop_chk.pack(anchor='w', padx=10, pady=5)
        loop_chk.config(style='Danger.TCheckbutton')
        ttk.Label(win, text='Hotkey:').pack(anchor='w', padx=10, pady=(10, 0))
        ttk.Combobox(win, width=4, state='readonly',
                     values=HOTKEY_OPTIONS, textvariable=self.hotkey_var).pack(anchor='w', padx=10, pady=5)
        ttk.Button(win, text='Close', command=win.destroy).pack(pady=10)
        style = ttk.Style(win)
        style.configure('Danger.TCheckbutton', foreground='red')

    def trigger_search(self):
        if not self.items:
            messagebox.showwarning('Warning', 'Add item first')
            return
        def run_items():
            for idx, item in enumerate(self.items):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    screenshot = pyautogui.screenshot()
                    screenshot.save(tmp.name)
                    finder = KeyleFinderModule(tmp.name)
                    result = finder.locate(item['path'], debug=self.debug_var.get())
                os.unlink(tmp.name)
                if result.get('status') == 0:
                    tl = result['top_left']
                    br = result['bottom_right']
                    center_x = (tl[0] + br[0]) // 2
                    center_y = (tl[1] + br[1]) // 2
                    pyautogui.moveTo(center_x, center_y)
                    if item.get('double_click'):
                        pyautogui.click(clicks=2)
                    else:
                        pyautogui.click()
                    self.log(f'Item {idx} matched at {center_x},{center_y}')
                else:
                    self.log(f'Item {idx} match failed')
            if self.loop_var.get():
                self.after(500, run_items)
        self.after(100, run_items)

    def on_close(self):
        keyboard.clear_all_hotkeys()
        self.destroy()


def main():
    App().mainloop()


if __name__ == '__main__':
    main()
