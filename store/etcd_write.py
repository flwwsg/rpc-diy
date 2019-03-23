import time
import etcd3


client = etcd3.client(host="localhost", port=2379)
t = time.time()
# client.delete("/demo", recursive=True)
client.put("/demo/%s" % int(t), str(t))
# print(client.read("/demo"))
