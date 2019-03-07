import json
import struct
import socket
import os
import _thread as thread


def handle_conn(conn: socket.socket, addr: str, handlers: dict):
    print(addr, "comes")
    print("in process pid = %s" % os.getpid())
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
        # thread.start_new_thread(handle_conn, (conn, addr, handlers))
        handle_conn(conn, addr, handlers)


def ping(conn: socket.socket, params: str):
    send_result(conn, "pong", params)


def send_result(conn: socket.socket, out: str, result):
    response = json.dumps({"out": out, "result": result})
    length_prefix = struct.pack("I", len(response))
    conn.sendall(length_prefix)
    conn.sendall(str.encode(response))


def prefork(n):
    for i in range(n):
        pid = os.fork()
        if pid < 0:
            # fork error
            return
        if pid > 0:
            # in parent process
            print("in process with child process pid = %s" % pid)
            continue
        if pid == 0:
            # in child process, preserve fork
            print("in child process")
            break


def prethread(n, sock, handlers):
    for i in range(n):
        thread.start_new_thread(loop, (sock, handlers))


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 打开 reuse addr   选项
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("localhost", 8080))
    sock.listen(1)
    # prefork
    # 之后，父进程创建的服务套接字引用，每个子进程也会继承一份，
    # 它们共同指向了操作系统内核的套接字对象，共享了同一份连接监听队列。
    # 子进程和父进程一样都可以对服务套接字进行 accept
    # 调用，从共享的监听队列中摘取一个新连接进行处理。
    prefork(10)
    # thread mod
    handlers = {
        "ping": ping,
    }
    loop(sock, handlers)
