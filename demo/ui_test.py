import tkinter as tk

def test_all_components():
    root = tk.Tk()

    # Label
    label = tk.Label(root, text="This is a Label")
    label.pack()

    # Button
    def button_click():
        print("Button clicked!")
    button = tk.Button(root, text="Click Me", command=button_click)
    button.pack()

    # Entry
    entry = tk.Entry(root)
    entry.pack()

    # Listbox
    listbox = tk.Listbox(root)
    for i in range(10):
        listbox.insert(tk.END, f"Item {i+1}")
    listbox.pack()

    # Scrollbar
    scrollbar = tk.Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text = tk.Text(root, yscrollcommand=scrollbar.set)
    for i in range(100):
        text.insert(tk.END, f"Line {i+1}\n")
    text.pack(side=tk.LEFT, fill=tk.BOTH)
    scrollbar.config(command=text.yview)

    root.mainloop()

if __name__ == "__main__":
    test_all_components()
