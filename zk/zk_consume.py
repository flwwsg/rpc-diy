import json
from kazoo.client import KazooClient

zk_root = "/demo"
zk = KazooClient(hosts="127.0.0.1:2181")
zk.start()
servers = set()
for child in zk.get_children(zk_root):
    node = zk.get(zk_root + "/" + child)
    addr = json.loads(node[0])
    servers.add("%s:%d" % (addr["host"], addr['port']))
servers = list(servers)