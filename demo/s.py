import socket
import time
import atexit

class SimpleServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None

    def start(self):
        # 创建一个TCP/IP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 绑定地址和端口
        server_address = (self.host, self.port)
        self.server_socket.bind(server_address)
        # 开始监听连接
        self.server_socket.listen(5)
        print("服务器启动，等待客户端连接...")

        try:
            while True:
                # 等待连接
                client_socket, client_address = self.server_socket.accept()
                print("客户端连接：", client_address)

                try:
                    while True:
                        # 接收消息
                        message = self.receive_message(client_socket)
                        if message is None:
                            print("客户端关闭连接")
                            break
                        print("收到消息：", message)

                        time.sleep(1)
                        # 发送回复消息
                        reply_message = "收到消息：{}".format(message)
                        self.send_message(client_socket, reply_message)
                finally:
                    # 关闭客户端连接
                    client_socket.close()
        finally:
            # 关闭服务器socket
            self.server_socket.close()

    def receive_message(self, client_socket):
        # 接收消息
        message = client_socket.recv(1024)
        # 如果收到的消息为空，说明客户端已关闭连接
        if not message:
            return None
        # 将收到的字节消息转换为字符串
        return message.decode('utf-8')

    def send_message(self, client_socket, message):
        # 发送消息
        client_socket.sendall(message.encode('utf-8'))

def main():
    # 创建 SimpleServer 实例并启动
    server = SimpleServer('localhost', 12582)
    # 注册在脚本退出时调用 close 方法
    atexit.register(server.server_socket.close)
    server.start()

if __name__ == "__main__":
    main()
