import socket

s = socket.socket()
host = "192.168.1.108"
port = 1776
s.connect((host, port))
print(s.recv(1024))
s.close()
