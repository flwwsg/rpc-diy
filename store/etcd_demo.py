from etcd import Client

client = Client(host="localhost", port=2379)
client.write("/demo/demo", 1)
print(client.read("/demo"))
for e in client.eternal_watch("/demo", recursive=True):
    print(e.value)

