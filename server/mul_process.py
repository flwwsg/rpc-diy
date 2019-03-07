import json
import struct
import socket
import os


def handle_conn(conn: socket.socket, addr: str, handlers: dict):
    print(addr, "comes")
    while True:
        length_prefix = conn.recv(4)
        if not length_prefix:
            # 连接关闭
            print(addr, "close")
            conn.close()
            break
        length, = struct.unpack("I", length_prefix)
        body = conn.recv(length)
        request = json.loads(body)
        in_ = request["in"]
        params = request["params"]
        print(in_, params)
        # 查找请求处理器
        handler = handlers[in_]
        handler(conn, params)


def loop(sock: socket.socket, handlers: dict):
    while True:
        conn, addr = sock.accept()
        pid = os.fork()
        if pid < 0:
            # error
            return
        if pid > 0:
            # in parent process
            conn.close()
            continue
        if pid == 0:
            # in child process
            sock.close()
            handle_conn(conn, addr, handlers)
            break


def ping(conn: socket.socket, params: str):
    send_result(conn, "pong", params)


def send_result(conn: socket.socket, out: str, result):
    response = json.dumps({"out": out, "result": result})
    length_prefix = struct.pack("I", len(response))
    conn.sendall(length_prefix)
    conn.sendall(str.encode(response))


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 打开 reuse addr   选项
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("localhost", 8080))
    sock.listen(1)
    handlers = {
        "ping": ping,
    }
    loop(sock, handlers)
