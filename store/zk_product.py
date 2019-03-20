import json
from kazoo.client import KazooClient

zk_root = "/demo"
zk = KazooClient(hosts="localhost:2181")
# 开始连接
zk.start()
value = json.dumps({"host": "127.0.0.1", "port": 8080})
# 确保节点存在
zk.ensure_path("/demo")
# 可以自动移除的节点
zk.create("/demo/rpc", str.encode(value), ephemeral=True, sequence=True)
print(zk.get_children(zk_root))
print(zk.get(zk_root+"/"+zk.get_children(zk_root)[0]))
