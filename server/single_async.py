import json
from io import StringIO
import asyncore
import socket
import struct


class RPCHandler(asyncore.dispatcher_with_send):

    def __init__(self, sock: socket.socket, addr: str):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self.addr = addr
        self.handlers = {
            "ping": self.ping
        }
        self.rbuf = StringIO()

    def handle_connect(self):
        # 连接被accept
        print(self.addr, "comes")

    def handle_close(self):
        # 有读事件时的回调方法
        print(self.addr, "close")
        self.close()

    def handle_read(self):
        while True:
            content = self.recv(1024)
            if content:
                self.rbuf.write(bytes.decode(content))
            if len(content) < 1024:
                # 读完本次缓存
                break
        self.handle_rpc()

    def handle_rpc(self):
        # 可能一次性收到了多个请求消息，所以需要循环处理
        while True:
            self.rbuf.seek(0)
            length_prefix = self.rbuf.read(4)
            if len(length_prefix) < 4:
                break
            length, = struct.unpack("I", str.encode(length_prefix))
            body = self.rbuf.read(length)
            if len(body) < length:
                # 不足一个消息
                break
            request = json.loads(body)
            in_ = request["in"]
            params = request["params"]
            print(in_, params)
            handler = self.handlers[in_]
            handler(params)
            # 消息处理完了，缓冲区要截断
            left = self.rbuf.getvalue()[length+4:]
            self.rbuf = StringIO()
            self.rbuf.write(left)
        # 将游标挪到文件结尾，以便后续读到的内容直接追加
        self.rbuf.seek(0,  2)

    def ping(self, params):
        self.send_result("pong", params)

    def send_result(self, out, result):
        response = {"out": out, "result": result}
        body = json.dumps(response)
        length_prefix = struct.pack("I", len(body))
        self.send(length_prefix)
        self.send(str.encode(body))


class RPCServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(1)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            RPCHandler(sock, addr)


if __name__ == '__main__':
    RPCServer("localhost", 8080)
    asyncore.loop()


