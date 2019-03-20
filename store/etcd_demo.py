import etcd3
import time
import _thread as thread


client = etcd3.client(host="localhost", port=2379)
client.put("/demo/demo", "1")
print(list(client.get_prefix("/demo")))


def watch_callback(event):
    print("update etcd")
    print(event)


# watch_id = client.add_watch_callback("/demo", watch_callback)
def watch_event(*args, **kwargs):
    event_iter, cance = client.watch_prefix("/demo/")
    for e in event_iter:
        print("updating etcd")
        print(e)


thread.start_new_thread(watch_event, (None, None))

# i = 0
# while True:
#     # print(1)
#     # i += 1
#     time.sleep(1)



