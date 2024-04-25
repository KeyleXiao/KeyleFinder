#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import cv2
import json
import atexit
import socket
import time
import tkinter as tk
from tkinter import ttk, messagebox
import base64
from PIL import Image, ImageTk
import io
import threading


class ServerStatus:
    NOT_STARTED = 0
    RUNNING = 1
    STOPPED = 2

class TCPServer:
    def __init__(self, ip, port,ui_instance):
        self.ip = ip
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.is_running = False
        self.ui_instance = ui_instance

    def start(self):
        # 创建TCP套接字
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 绑定IP和端口
        self.server_socket.bind((self.ip, self.port))
        # 开始监听
        self.server_socket.listen(5)
        self.is_running = True
        print(f"Server is listening on {self.ip}:{self.port}...")

        # 启动线程处理连接
        server_thread = threading.Thread(target=self.accept_connections)
        server_thread.daemon = True
        server_thread.start()

    def accept_connections(self):
        while self.is_running:
            try:
                # 接受连接
                self.client_socket, self.client_address = self.server_socket.accept()
                print(f"Accepted connection from {self.client_address}")

                # 处理客户端连接
                client_thread = threading.Thread(target=self.handle_client)
                client_thread.start()

            except KeyboardInterrupt:
                print("Server stopped by user.")
                self.stop()
            except Exception as e:
                print(f"Error accepting connection: {e}")

    def handle_client(self):
        try:
            while self.is_running:
                # 接收消息
                data = self.client_socket.recv(1024)
                if not data:
                    break
                # print(f"Received from client: {data.decode()}")
                self.ui_instance.receive_message(data)
                # 发送消息回客户端
                # message = input("Enter message to send back to client: ")
                # self.client_socket.sendall(message.encode())

        except ConnectionResetError:
            print("Client disconnected.")
        finally:
            # 关闭客户端套接字
            self.client_socket.close()

    def stop(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        print("Server stopped.")


class KeyleKitService:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.image_preview_window = None
        self.RenderGUI()


    def RenderGUI(self):
        self.root = tk.Tk()
        self.root.title("KCP Demo Server")
        self.root.protocol("WM_DELETE_WINDOW", self.closeServer)

        # 服务器地址标签
        self.address_frame = ttk.Frame(self.root)
        self.address_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.address_label = ttk.Label(self.address_frame, text="Server Address:")
        self.address_label.pack(side="left")
        self.address_text = tk.StringVar()
        self.address_text.set("Not Started")
        self.address_label_text = ttk.Label(self.address_frame, textvariable=self.address_text, foreground="gray")
        self.address_label_text.pack(side="left")

        # 创建右侧文本框用于显示收到的消息
        self.received_text = tk.Text(self.root, height=20, width=45)
        self.received_text.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

        # # 创建 message_listbox
        self.message_listbox = tk.Listbox(self.root)
        self.message_listbox.grid(row=2, column=2, padx=5, pady=5, sticky="nsew")

        # 创建列表视图用于显示收到的消息列表
        self.message_listbox.bind("<<ListboxSelect>>", self.select_message)

        # 创建清除按钮
        self.clear_button = ttk.Button(self.root, text="Clear History Messages", command=self.clear_messages)
        self.clear_button.grid(row=3, column=2, padx=5, pady=5, sticky="ew")

        # 服务器状态图标和描述
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.status_label = ttk.Label(self.status_frame, text="Server Status:")
        self.status_label.pack(side="left")
        self.status_text = tk.StringVar()
        self.status_label_text = ttk.Label(self.status_frame, textvariable=self.status_text, foreground="gray")
        self.status_label_text.pack(side="left")

        # 创建左侧文本框用于发送消息
        self.send_text = tk.Text(self.root, height=20, width=45)
        self.send_text.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        # 创建发送按钮
        self.send_button = ttk.Button(self.root, text="Send Message", command=self.send_message)
        self.send_button.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        # 创建右侧文本框用于显示收到的消息
        self.received_text = tk.Text(self.root, height=20, width=45)
        self.received_text.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

        # 创建预览图片按钮
        self.preview_button = ttk.Button(self.root, text="Try Preview Image", command=self.check_base64_and_preview)
        self.preview_button.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # 设置网格布局的权重，使得窗口大小变化时文本框可以扩展
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_columnconfigure(1, weight=1)

    def set_server_status(self, status):
        if status == ServerStatus.RUNNING:
            self.status_text.set("Running")
            self.status_label_text.config(foreground="green")
        elif status == ServerStatus.STOPPED:
            self.status_text.set("Stopped")
            self.status_label_text.config(foreground="red")
        else:
            self.status_text.set("Not Started")
            self.status_label_text.config(foreground="gray")


    def check_base64_and_preview(self):
        text = self.received_text.get("1.0", "end").strip()
        try:
            # Decode base64 string to bytes
            image_bytes = base64.b64decode(text)
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            # Display image in a new window
            self.show_image_preview(image)
        except Exception as e:
            print("Error:", e)
            messagebox.showerror("Error", "Failed to decode base64 string or display image.")

    def show_image_preview(self, image):
        # Create a new window for image preview
        self.image_preview_window = tk.Toplevel(self.root)
        self.image_preview_window.title("Image Preview")

        # Convert image to Tkinter PhotoImage
        image_tk = ImageTk.PhotoImage(image)

        # Display image in a label
        label = tk.Label(self.image_preview_window, image=image_tk)
        label.image = image_tk  # Keep a reference to avoid garbage collection
        label.pack()


    def set_server_status(self, status, address=None):
        if status == ServerStatus.RUNNING:
            self.status_text.set("Running")
            self.status_label_text.config(foreground="green")
            if address:
                self.address_text.set(address)
        elif status == ServerStatus.STOPPED:
            self.status_text.set("Stopped")
            self.status_label_text.config(foreground="red")
            if address:
                self.address_text.set(address)
        else:
            self.status_text.set("Not Started")
            self.status_label_text.config(foreground="gray")
            self.address_text.set("Not Started")

    def add_message_to_list(self, message):
        # 添加消息到列表视图
        current_time = time.strftime("%H:%M", time.localtime())
        self.message_listbox.insert(tk.END, f"{current_time}:{message}")

    def select_message(self, event):
        # 检查是否有选中的项
        if self.message_listbox.curselection():
            # 获取选中的索引
            index = self.message_listbox.curselection()[0]
            message = self.message_listbox.get(index)
            self.received_text.delete("1.0", tk.END)
            self.received_text.insert(tk.END, message)

    def clear_messages(self):
        # 清除消息列表中的所有项
        self.message_listbox.delete(0, tk.END)

    def closeServer(self):
        self.TCPServer.stop()
        self.TCPServer.stop()
        self.server_run = ServerStatus.STOPPED
        self.root.destroy()

    def start(self):
        self.server_run = ServerStatus.RUNNING
        self.set_server_status(self.server_run, "{0}:{1}".format(self.host, self.port))
        # # 注册在脚本退出时调用 close 方法
        # atexit.register(self.server_socket.close)
        self.TCPServer = TCPServer(self.host, self.port,self)
        self.TCPServer.start()
        self.root.mainloop()

    def receive_message(self, message):
        if not message:
            return
        # 将收到的字节消息转换为字符串
        # message.decode('utf-8')
        self.add_message_to_list(message)


    def send_message(self, message):
        message = self.send_text.get("1.0", tk.END).strip()
        if message:
            print("Sending message:", message)
            # 在这里可以实现发送消息到 Unity 的代码
            self.send_text.delete("1.0", tk.END)
            # 发送消息
            # client_socket.sendall(message.encode('utf-8'))
            self.TCPServer.sendall(message.encode())



if __name__ == "__main__":
    server = KeyleKitService('localhost', 12582)
    server.start()


