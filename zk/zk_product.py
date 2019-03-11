import json
from kazoo.client import KazooClient

zk = KazooClient(hosts="localhost:2181")
zk.start()
value = json.dumps({"host": "127.0.0.1", "port":8080})
zk.ensure_path("/demo")
# 自动移除过期节点 （临时节点）， 顺序节点 (sequence)，它可以在节点名称后面自动追加自增 id，避免节点名称重复
zk.create("/demo/rpc", value, ephemeral=True, sequence=True)
zk.stop()
