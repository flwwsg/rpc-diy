import time
import random
import socket
import json
import struct
from kazoo.client import KazooClient

zk_root = "/demo"
# 全局变量，RemoteServer 对象列表
G = {"servers": None}


class RemoteServer(object):
    def __init__(self, addr):
        self.addr = addr
        self._socket = None

    @property
    def socket(self):
        if not self._socket:
            self.connect()
        return self._socket

    def ping(self, twitter):
        return self.rpc("ping", twitter)

    def pi(self, n):
        return self.rpc("pi", n)

    def rpc(self, in_, params):
        sock = self.socket
        request = json.dumps({"in": in_, "params": params})
        length_prefix = struct.pack("I", len(request))
        sock.send(length_prefix)
        sock.sendall(str.encode(request))
        length_prefix = sock.recv(4)
        length, = struct.unpack("I", length_prefix)
        body = sock.recv(length)
        response = json.loads(body)
        return response["out"], response["result"]

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host, port = self.addr.split(":")
        sock.connect((host, int(port)))
        self._socket = sock

    def reconnect(self):
        self.close()
        self.connect()

    def close(self):
        if self._socket:
            self._socket.close()
            self._socket = None


def get_servers():
    zk = KazooClient()
    zk.start()
    # 当前活跃地址
    current_addrs = set()

    def watch_servers(*args):
        print("listening zk")
        new_addrs = set()
        # 获取新的服务地址，并监听服务变动
        for child in zk.get_children(zk_root, watch=watch_servers):
            node = zk.get(zk_root+"/"+child)
            addr = json.loads(node[0])
            new_addrs.add("%s:%d" % (addr["host"], addr["port"]))
        # 新增
        add_addrs = new_addrs - current_addrs
        # 需要删除
        del_addrs = current_addrs - new_addrs
        del_servers = []
        for addr in del_addrs:
            for s in G["servers"]:
                if s.addr == addr:
                    del_servers.append(s)
                    break
        for server in del_servers:
            G["servers"].remove(server)
            current_addrs.remove(server.addr)
        # 新增
        for addr in add_addrs:
            G["servers"].append(RemoteServer(addr))
            current_addrs.add(addr)

    for child in zk.get_children(zk_root, watch=watch_servers):
        node = zk.get(zk_root+"/"+child)
        addr = json.loads(node[0])
        current_addrs.add("%s:%d" % (addr["host"], addr["port"]))
    G["servers"] = [RemoteServer(s) for s in current_addrs]
    print("last g[servers]", G["servers"])
    return G["servers"]


def random_server():
    if G["servers"] is None:
        get_servers()
    if not G["servers"]:
        return
    return random.choice(G["servers"])


if __name__ == '__main__':
    for i in range(100):
        print(G["servers"])
        server = random_server()
        if not server:
            # 没有节点
            print("no node alive")
            break
        print("in server ", server.addr)
        time.sleep(.5)
        try:
            out, result = server.ping("reader %d" % i)
            print(server.addr, out, result)
        except Exception as e:
            server.close()
            print(e)
        server = random_server()
        if not server:
            break
        time.sleep(0.5)
        try:
            out, result = server.pi(i)
            print(server.addr, out, result)
        except Exception as e:
            server.close()
            print(e)
