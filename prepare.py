# socket
import socket
import struct

# client
sock = socket.socket()
sock.connect(("localhost", 8080))
sock.recv(1024)
sock.send()
sock.sendall()
sock.close()

# server
sock = socket.socket()
sock.bind(("localhost", 8080))
sock.listen()
sock.accept()
sock.close()


# 将一个整数编码成 4 个字节的字符串， I 代表格式
value_in_bytes = struct.pack("I", 1024)
value, = struct.unpack("I", value_in_bytes)
# 注意等号前面有个逗号，这个非常重要，它不是笔误。
# 因为 unpack 返回的是一个列表，它可以将一个很长的字节串解码成一系列的对象。
# value 取这个列表的第一个对象。