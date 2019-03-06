
import json
import time
import struct
import socket


# 我们将使用长度前缀法来确定消息边界，消息体使用 json 序列化。
# 每个消息都有相应的名称，请求的名称使用 in 字段表示，请求的参数使用
# params 字段表示，响应的名称是 out 字段表示，
# 响应的结果用 result 字段表示。
def rpc(sock: socket.socket, in_: str, params: str):
    # 请求消息体
    request = json.dumps({"in": in_, "params": params})
    # 长度前缀法对请求消息进行编码
    length_prefix = struct.pack("I", len(request))
    sock.sendall(length_prefix)
    sock.sendall(str.encode(request))
    # 响应长度前缀
    length_prefix = sock.recv(4)
    length, = struct.unpack("I", length_prefix)
    # 响应消息体
    body = sock.recv(length)
    response = json.loads(body)
    return response["out"], response["result"]


# 默认是阻塞调用，不过这个阻塞也是有条件的。
# 如果内核的套接字接收缓存是空的，它才会阻塞。
# 只要里面有哪怕只有一个字节，这个方法就不会阻塞，
# 它会尽可能将接受缓存中的内容带走指定的字节数，
# 然后就立即返回，而不是非要等待期望的字节数全满足了才返回
# 这意味着我们需要尝试循环读取才能正确地读取到期望的字节数
def receive(sock, n):
    all_result = []
    while n > 0:
        r = sock.recv(n)
        if not r:
            return all_result
        all_result.append(r)
        n -= len(r)
    return ''.join(all_result)


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 8080))
    for i in range(4):
        out, result = rpc(s, "fib", i)
        print(out, result)
        time.sleep(1)
    s.close()
