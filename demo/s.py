import socket
import threading

class TCPServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.is_running = False

    def start(self):
        # 创建TCP套接字
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 绑定IP和端口
        self.server_socket.bind((self.ip, self.port))
        # 开始监听
        self.server_socket.listen(1)
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
                print(f"Received from client: {data.decode()}")

                # 发送消息回客户端
                message = input("Enter message to send back to client: ")
                self.client_socket.sendall(message.encode())

        except ConnectionResetError:
            print("Client disconnected.")
        finally:
            # 关闭客户端套接字
            self.client_socket.close()

    def stop(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()
        print("Server stopped.")

# 使用示例
# if __name__ == "__main__":
#     server = TCPServer("127.0.0.1", 8888)
#     server.start()
#
#     # 假设这是一个无限循环，以保持主线程运行，直到你决定停止服务器
#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         print("Stopping server...")
#         server.stop()