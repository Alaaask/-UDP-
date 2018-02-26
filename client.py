# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 14:33:07 2017

@author: yu
"""

import socket
import threading
import time
import os

# 客户端和服务器的ip都是一样的，是我的ip
myhost = socket.gethostbyname(socket.gethostname())

HOST = myhost
PORT = 50007 # 服务器端口


with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    
    # connect了就不能接收其他套接字发来的消息了
    s.connect((HOST, PORT))
    s.setblocking(0)
    
    def send(s):
        while True:
            message = input("\n")
            if message == "/exit":
                os._exit(0)
            s.sendto(message.encode('utf-8'), (HOST, PORT))
    
    def receive(s):
        while True:
            try:
                response = s.recv(1024)
                print ("=====================================================")
                print ("From server:\n" + response.decode('utf-8'))
                print ("=====================================================")
            except:
                time.sleep(2)
    
    t1 = threading.Thread(target=send, args = (s, ))
    t2 = threading.Thread(target=receive, args = (s, ))

    t1.start()
    t2.start()
    
    t1.join()
    