import time
from etcd import Client

client = Client(host="localhost", port=2379)
t = time.time()
client.write("/demo/%s" % int(t), t)
print(client.read("/demo"))
