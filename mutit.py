import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import os
import pyautogui
import tempfile
from typing import List

from KeyleFinderModule import KeyleFinderModule


class Task:
    def __init__(self, image_path: str, clear_screen: bool = False):
        self.image_path = image_path
        self.clear_screen = tk.BooleanVar(value=clear_screen)


class MultiLocatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Multi Locator")
        self.geometry("260x360")
        self.resizable(False, False)

        self.tasks: List[Task] = []

        self.interval_var = tk.IntVar(value=0)
        self.loop_var = tk.BooleanVar(value=False)
        self.debug_var = tk.BooleanVar(value=False)

        self.create_widgets()

    def create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=5)
        ttk.Button(top, text="Add", command=self.add_task).pack(side="left", padx=2)
        ttk.Button(top, text="Start", command=self.start_tasks).pack(side="left", padx=2)
        ttk.Button(top, text="Settings", command=self.open_settings).pack(side="right", padx=2)

        self.task_frame = ttk.Frame(self)
        self.task_frame.pack(fill="both", expand=True, pady=5)

    def add_task(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.jpeg")])
        if not path:
            return
        task = Task(path)
        self.tasks.append(task)
        row = ttk.Frame(self.task_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=os.path.basename(path)).pack(side="left", padx=4)
        ttk.Checkbutton(row, text="Clear Screen", variable=task.clear_screen).pack(side="right")

    def open_settings(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.resizable(False, False)

        def on_interval_change(*_):
            if self.interval_var.get() > 0:
                self.loop_var.set(False)

        def on_loop_toggle(*_):
            if self.loop_var.get():
                self.interval_var.set(0)

        self.interval_var.trace_add("write", on_interval_change)
        self.loop_var.trace_add("write", on_loop_toggle)

        ttk.Label(win, text="Interval (sec):").pack(anchor="w", padx=10, pady=5)
        ttk.Entry(win, textvariable=self.interval_var, width=8).pack(anchor="w", padx=10)
        tk.Checkbutton(win, text="Repeat Execute", variable=self.loop_var).pack(anchor="w", padx=10, pady=5)
        ttk.Checkbutton(win, text="Debug", variable=self.debug_var).pack(anchor="w", padx=10, pady=5)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def start_tasks(self):
        if not self.tasks:
            messagebox.showwarning("Warning", "Add tasks first")
            return
        self.iconify()
        self.after(100, self.run_next_task, 0)

    def run_next_task(self, index: int):
        if index >= len(self.tasks):
            if self.loop_var.get():
                self.after(0 if self.interval_var.get() == 0 else self.interval_var.get() * 1000,
                           self.run_next_task, 0)
            else:
                self.deiconify()
            return
        task = self.tasks[index]
        if task.clear_screen.get():
            pyautogui.hotkey('win', 'd')
            time.sleep(0.5)
        self.execute_task(task)
        delay = self.interval_var.get() * 1000
        self.after(delay, self.run_next_task, index + 1)

    def execute_task(self, task: Task):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            screenshot = pyautogui.screenshot()
            screenshot.save(tmp.name)
            finder = KeyleFinderModule(tmp.name)
            result = finder.locate(task.image_path, debug=self.debug_var.get())
        os.unlink(tmp.name)
        if result.get('status') == 0:
            tl = result['top_left']
            br = result['bottom_right']
            center_x = (tl[0] + br[0]) // 2
            center_y = (tl[1] + br[1]) // 2
            pyautogui.moveTo(center_x, center_y)
            pyautogui.click()


def main():
    app = MultiLocatorApp()
    app.mainloop()


if __name__ == '__main__':
    main()
