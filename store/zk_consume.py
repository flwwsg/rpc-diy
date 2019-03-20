import json
from kazoo.client import KazooClient

zk_root = "/demo"
zk = KazooClient()
zk.start()
servers = set()
print(zk.get_children(zk_root))
for child in zk.get_children(zk_root):
    node = zk.get(zk_root+"/"+child)
    print("node in zk", node)
    addr = json.loads(node[0])
    servers.add("%s:%d" %(addr["host"], addr["port"]))
servers = list(servers)
zk.stop()
