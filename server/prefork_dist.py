import sys
import json
import errno
import signal
import math
from io import StringIO
import asyncore
import socket
import struct
import os
from kazoo.client import KazooClient
from etcd import Client


class RPCHandler(asyncore.dispatcher_with_send):

    def __init__(self, sock: socket.socket, addr: str):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self.addr = addr
        self.handlers = {
            "ping": self.ping,
            "pi": self.pi
        }
        self.rbuf = StringIO()

    def handle_connect(self):
        # 连接被accept
        print(self.addr, "comes")

    def handle_close(self):
        print(self.addr, "close")
        self.close()

    # 有读事件时的回调方法
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
                # 半包
                break
            length, = struct.unpack("I", str.encode(length_prefix))
            body = self.rbuf.read(length)
            if len(body) < length:
                # 不足一个消息
                break
            request = json.loads(body)
            in_ = request["in"]
            params = request["params"]
            print(os.getpid(), in_, params)
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

    def pi(self, n):
        s = 0.0
        for i in range(n+1):
            s += 1.0/(2*i+1)/(2*i+1)
        res = math.sqrt(8*s)
        self.send_result("pi_r", res)

    def send_result(self, out, result):
        response = {"out": out, "result": result}
        body = json.dumps(response)
        length_prefix = struct.pack("I", len(body))
        self.send(length_prefix)
        self.send(str.encode(body))


class RPCServer(asyncore.dispatcher):
    zk_root = "/demo"
    zk_rpc = zk_root + "/rpc"

    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(("localhost", port))
        self.listen(1)
        self.child_pids = None
        self.zk = KazooClient()
        self.etcd = Client(port=2379)
        self.port = port
        if self.prefork(10):
            # self.register_zk(port)
            self.register_etcd()
            self.register_parent_signal()
        else:
            # in child process, pid = 0
            self.register_child_signal()

    def prefork(self, n):
        for i in range(n):
            pid = os.fork()
            if pid < 0:
                raise Exception("fork error")
            if pid > 0:
                # in parent process
                if self.child_pids:
                    self.child_pids.append(pid)
                else:
                    self.child_pids = [pid]
                continue
            if pid == 0:
                # in child process
                return False
        return True

    def register_zk(self, port):
        self.zk.start()
        # 确保节点存在
        self.zk.ensure_path(self.zk_root)
        value = json.dumps({"host": "127.0.0.1", "port": port})
        # 可以自动移除的节点
        self.zk.create("/demo/rpc", str.encode(value), ephemeral=True, sequence=True)
        child = self.zk.get_children(self.zk_root)
        print("node in zk are:")
        for c in child:
            print(self.zk.get(self.zk_root+"/"+c)[0])

    def register_etcd(self):
        value = json.dumps({"host": "127.0.0.1", "port": self.port})
        res = self.etcd.write(self.zk_rpc + "/localhost:%s" % self.port, value)
        directory = self.etcd.get(self.zk_rpc)
        for d in directory.leaves:
            print(d.key, ":", d.value)

    def exit_parent(self, sig, frame):
        # self.zk.stop()
        self.etcd.delete(self.zk_rpc + "/localhost:%s" % self.port)
        self.close()
        asyncore.close_all()
        pids = []
        for pid in self.child_pids:
            print("before kill")
            try:
                # 中止子进程
                os.kill(pid, signal.SIGINT)
                pids.append(pid)
            except OSError as ex:
                if ex.args[0] == errno.ECHILD:
                    # 目标子进程已经提前挂了
                    continue
                raise ex
            print("after kill", pid)
        for pid in pids:
            while True:
                try:
                    os.waitpid(pid, 0)
                    break
                except OSError as ex:
                    if ex.args[0] == errno.ECHILD:
                        # 子进程已经割过了
                        break
                    if ex.args[0] != errno.EINTR:
                        # 被其它信号打断了
                        raise ex
            print("wait over", pid)

    def reap_child(self, sig, frame):
        # 监听子进程退出
        print("before reap")
        info = None
        while True:
            try:
                info = os.waitpid(-1, os.WNOHANG)
                break
            except OSError as ex:
                if ex.args[0] == errno.ECHILD:
                    # 子进程已经割过了
                    break
                if ex.args[0] != errno.EINTR:
                    # 被其它信号打断了
                    raise ex
        if info:
            pid = info[0]
            try:
                self.child_pids.remove(pid)
            except ValueError:
                pass
            print("after reap", pid)

    def register_parent_signal(self):
        signal.signal(signal.SIGINT, self.exit_parent)
        signal.signal(signal.SIGTERM, self.exit_parent)
        signal.signal(signal.SIGCHLD, self.reap_child)

    def exit_child(self, sig, frame):
        self.close()
        asyncore.close_all()
        print("child all closed")

    def register_child_signal(self):
        signal.signal(signal.SIGINT, self.exit_child)
        signal.signal(signal.SIGTERM, self.exit_child)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            RPCHandler(sock, addr)


if __name__ == '__main__':
    port = int(sys.argv[1])
    RPCServer(port)
    asyncore.loop()


