import os
import json
import struct
import socket


def handle_conn(conn: socket.socket,  addr, handlers):
    print(addr, "comes")
    while True:
        length_prefix = conn.recv(4)
        if not length_prefix:
            print(addr, "close")
            conn.close()
            break
        length, = struct.unpack("I", length_prefix)
        body = conn.recv(length)
        request = json.loads(body)
        in_ = request["in"]
        params = request['params']
        print(in_, params)
        handler = handlers[in_]
        handler(conn, params)


def loop_slave(pr, handlers):
    while True:
        bufsize = 1
        # 计算长度
        ancsize = socket.CMSG_LEN(struct.calcsize("i"))
        msg, ancdata, flags, addr = pr.recvmsg(bufsize, ancsize)
        cmsg_level, cmsg_type, cmsg_data = ancdata[0]
        fd = struct.unpack('i', cmsg_data)[0]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, fileno=fd)
        handle_conn(sock, sock.getpeername(), handlers)


def ping(conn, params):
    send_result(conn, "pong", params)


def send_result(conn, out, result):
    response = json.dumps({"out": out, "result": result}).encode('utf-8')
    length_prefix = struct.pack("I", len(response))
    conn.sendall(length_prefix)
    conn.sendall(response)


def loop_master(serv_sock, pws):
    idx = 0
    while True:
        sock, addr = serv_sock.accept()
        pw = pws[idx % len(pws)]
        msg = [b'x']
        ancdata = [(
            socket.SOL_SOCKET,
            socket.SCM_RIGHTS,
            struct.pack("i", sock.fileno())
        )]
        # ancdata 参数是一个三元组的列表，三元组的第一个参数表示网络协议栈级别
        # level，第二个参数表示辅助数据的类型
        # type，第三个参数才是携带的数据，level = SOL_SOCKET表示传递的数据处于 TCP
        # 协议层级，
        # type = SCM_RIGHTS
        # 就表示携带的数据是文件描述符。我们传递的描述符 fd
        # 是一个整数，需要使用struct 包将它序列化成二进制。, 序列化格式见
        # https://docs.python.org/3/library/struct.html
        pw.sendmsg(msg, ancdata)
        sock.close()
        idx += 1


def prefork(serv_sock, n):
    pws = []
    for i in range(n):
        pr, pw = socket.socketpair()
        pid = os.fork()
        if pid < 0:
            return pws
        if pid > 0:
            # 父进程
            pr.close()  # 父进程不用读
            pws.append(pw)
            continue
        if pid == 0:
            # 子进程
            pw.close()  # 子进程不用写
            serv_sock.close()
            return pr
    return pws


if __name__ == '__main__':
    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv_sock.bind(("localhost", 8080))
    serv_sock.listen(1)
    pws_or_pr = prefork(serv_sock, 10)
    print(pws_or_pr)
    if hasattr(pws_or_pr, '__len__'):
        # 返回父进程
        if pws_or_pr:
            loop_master(serv_sock, pws_or_pr)
        else:
            serv_sock.close()
    else:
        # 返回子进程
        handlers = {
            "ping": ping
        }
        loop_slave(pws_or_pr, handlers)


