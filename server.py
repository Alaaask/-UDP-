# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 14:21:41 2017

@author: yu
"""

import threading
import socket
import os
from collections import OrderedDict

# -------------------------------- 数据结构 --------------------------------

# 维护已登录用户的ip地址和端口
# 在每次登录时会动态改变
# 服务器给用户发送消息时，寻找用户在这里注册的地址和端口
# 然后通过一个UDP的socket
usersAddr = {}

# 用户ID和用户名
# 最多101个用户
# key = userID value = userName
# 根据题意，应该是userName也要保持唯一性
users = OrderedDict([('000','Tom'),('001','Jenny'),('002','Amy')])

# 维护用户行为数据——behaviors
# Behavior类
class Behavior:
    
    def __init__(self):
        self.logIn = False
        self.position = ''
    
    def log_in(self):
        self.logIn = True

    # 这个函数实际上没有用到，因为要求里没有写要logout      
    def log_out(self):
        self.logIn = False
    
    def get_log_state(self):
        return self.logIn
        
    def enter_shop(self, shopname):
        self.position = shopname
    
    def leave_shop(self):
        self.position = ''
        
    def get_position(self):
        return self.position
        
behaviors = OrderedDict()

# Good类
# shopname = userID
class Good:
    
    def __init__(self):
        self.gid = []
        self.gname = []
        self.gprice = []
        
    def add_goods(self, goodid, goodname, goodprice): # list是可重复的
        self.gid.append(goodid)
        self.gname.append(goodname)
        self.gprice.append(goodprice)
    
    # 判断有没有这件商品
    def has_good(self, goodsID):
        try:
            self.gid.index(goodsID)
        except:
            return False
        return True
    
    def get_goods_info(self):
        count = len(self.gid)
        message = ""
        if count != len(self.gname) or count != len(self.gprice):
            message += "Something wrong with the goods infomation."
        elif count == 0:
            message += "There is no goods information."
        else:
            message += ("Goods information of SHOP:\n")
            for i in range(count):
                message += (str(self.gid[i]) + ' ' + str(self.gname[i]) + ' ' + str(self.gprice[i]) + '\n')
        return message
    # 销毁就调用del

# Shop类
class Shop:
    
    def __init__(self, mygoods):
        self.goods = mygoods
        self.customerlist = []
        
    def get_customerID_list(self):
        return self.customerlist
        
    def get_customer_list(self):
        message = ""
        for customer in self.customerlist:
            message += (str(users[customer]) + " ")
        return message
        
    def customer_come(self, customerID):
        self.customerlist.append(customerID)
    
    def customer_leave(self, customerID):
        self.customerlist.remove(customerID)
            
                  
# 每个元素是一个Shop类的实例
shops = {'000': Shop(Good()),
         '001': Shop(Good())}
shops['000'].goods.add_goods("T1", "夹克", 455)
shops['001'].goods.add_goods("T2", "针织衫", 765)
shops['001'].goods.add_goods("S1", "A字裙", 299)


# ----------------------------- 线程1:读取管理员命令 -----------------------------
# 对于管理员命令的处理会出现在服务端
# 对于客户端的响应出现在客户端

def administrator(fromClient):
    
    def send_msg_to(message, shopname, fromClient):
        # 在用户的该UDP端口正在监听的情况下才可能发送成功
        # 也就是说正处于登录状态
        if shopname in usersAddr:
            
            clientHost = usersAddr[shopname][0]
            clientPort = usersAddr[shopname][1]
            
            fromClient.sendto(message.encode('utf-8'), (clientHost, clientPort))
        
    def send_msg_to_all(message, fromClient):
        
        for key in usersAddr: # 没登录的发不了
            send_msg_to(message, key, fromClient)
    
    while True:
        
        command = input("Please input your command:\n")
        
        if command == "/exit":
            os._exit(0)
            
        if command.find("/users") == 0:
            print ("We have users:")
            for key in users:
                if key in shops:
                    print (key + '-' + users[key] + '*')
                else:
                    print (key + '-' + users[key])
            print ("--------------------------------------------")
            
        elif command.find("/shops") == 0:
            print("We have shops(shopname = userID):")
            for key in shops:
                print (key)
            print ("--------------------------------------------")
        
        elif command.find("/opennewshop") == 0:
            shopname = str(command[13:])
            if shopname not in users:
                print("This is an invalid userID. We can not open a new shop.")
            else:
                shops[shopname] = Shop(Good())
                print("Successfully opened a new shop.")
                message = "You opened a shop in our eMall, your shop name is " + shopname + "."
                send_msg_to(message, shopname, fromClient)
            print ("--------------------------------------------")
            
        elif command.find("/msg") == 0:
            message = input("Please input your message:\n")
            if command == "/msg":
                send_msg_to_all(message, fromClient)
            else:
                userID = command[5:]
                if userID not in users:
                    print("Invalid userID.")
                else:
                    send_msg_to(message, userID, fromClient)
            print ("--------------------------------------------")
            
        elif command.find("/enter") == 0:
            shopname = command[7:]
            if shopname not in shops:
                print("The shop does not exist!")
            else:
                print("You have entered this shop!")
                while True:
                    commandInShop = input("What do you want to do in the shop?\nEnter '/leave' to leave the shop.\n")
                    if commandInShop == "/leave":
                        break
                    elif commandInShop == "/goods":
                        print(shops[shopname].goods.get_goods_info())
                    elif commandInShop == "/customers":
                        print(shops[shopname].get_customer_list())
                    else:
                        print("Invalid command.")
            print ("--------------------------------------------")
            
        elif command.find("/closeshop") == 0:
            shopname = command[11:]
            if shopname not in shops:
                print("The shop does not exist!")
            else:
                # 通知每个逛店的客户
                for customer in shops[shopname].get_customerID_list():
                    fromClient.sendto("Sorry, the shop will be closed.".encode('utf-8'), usersAddr[customer])
                    behaviors[customer].leave_shop()
                # 通知老板
                fromClient.sendto("Your shop will be closed.".encode('utf-8'), usersAddr[shopname])
                del shops[shopname]
            print ("--------------------------------------------")
            
        else:
            print("Invalid command!")
    
            
# ----------------------------- 线程2:响应客户端需求 -----------------------------
# 服务器总是在端口50007等待
# 我好像把所有都留在服务器处理了


def client(fromClient):
    
    # 根据用户名找用户ID
    def find_userID_from_userName(userName):
        
        key = ''
        for key in users:
            if users[key] == userName:
                return key
        return ''
    
    # 服务器自动生成唯一用户ID
    def get_nextid():
        
         return str(len(users)).zfill(3)
    
    # 根据用户地址和端口找用户ID
    # 这是因为服务器只能通过地址和端口号来区分不同用户
    def find_userID_from_addr(clientAddr):
        
        key = ''
        for key in usersAddr:
            if usersAddr[key] == clientAddr:
                return key
        return ''
    
    # 根据地址和接口判断是否已经登录
    # 返回用户ID
    def has_logged_in(clientAddr):
        userID = find_userID_from_addr(clientAddr)
        if userID != '' and userID in behaviors and behaviors[userID].get_log_state():
            return userID
        else:
            return ''
    
    # 返回信息
    M0 = "Successfully operated!"
    M1 = "You have not logged in yet."
    M2 = "This shop does not exist."
    M3 = "Please enter a shop first."
    M4 = "Please do not duplicate login."
    M5 = "Invalid request!"
    M6 = "This is the first time you have logged in."
    M7 = "You should open a shop first."
        
    while True:
        # 先登录
        request, clientAddr = fromClient.recvfrom(1024)
        request = request.decode('utf-8')
        
        # 同一个地址和端口不可重复登录不同账号
        if request.find('/login') == 0:
            # 如果同一账号在多地登录，以最后一个为准
            if has_logged_in(clientAddr):
                fromClient.sendto(M4.encode('utf-8'), clientAddr)
                continue
            userName = request[7:]
            if find_userID_from_userName(userName) == '':
                fromClient.sendto(M6.encode('utf-8'), clientAddr) # 第一次登录
                userID = get_nextid()
                users[userID] = userName # 为新用户分配userID
                behaviors[userID] = Behavior()
                behaviors[userID].log_in() #登录
                usersAddr[userID] = clientAddr # 更新用户地址和端口信息
            else:
                userID = find_userID_from_userName(userName)
                fromClient.sendto(M0.encode('utf-8'), clientAddr) # 成功登录
                behaviors[userID] = Behavior()
                behaviors[userID].log_in() #登录
                usersAddr[userID] = clientAddr # 更新用户地址和端口信息
                
        elif request == "/shops":
            if not has_logged_in(clientAddr):
                fromClient.sendto(M1.encode('utf-8'), clientAddr) # 未登录
                continue
            message = ""
            for key in shops:
                message += ("shopname/userID: {0}  userName: {1}\n".format(key, users[key]))
            fromClient.sendto(message.encode('utf-8'), clientAddr)
        
        # 这里enter不推送商品信息，而是通过/goods命令!
        elif request.find('/enter') == 0:
            userID = has_logged_in(clientAddr)
            if userID == '':
                fromClient.sendto(M1.encode('utf-8'), clientAddr) # 未登录
                continue                   
            shopname = request[7:]
            if shopname not in shops:
                fromClient.sendto(M2.encode('utf-8'), clientAddr) # 没有这个店
                continue
            fromClient.sendto(M0.encode('utf-8'), clientAddr) # 成功
            # 进店
            shops[shopname].customer_come(userID)
            behaviors[userID].enter_shop(shopname)
            # 向商店老板发消息
            if shopname in usersAddr:
                message = users[userID] + " comes into your shop."
                fromClient.sendto(message.encode('utf-8'), usersAddr[shopname])

        elif request == "/goods":
            userID = has_logged_in(clientAddr)
            if userID == '':
                fromClient.sendto(M1.encode('utf-8'), clientAddr) # 未登录
                continue
            if userID in behaviors:
                shopname = behaviors[userID].get_position()
                if shopname != '':
                    fromClient.sendto(shops[shopname].goods.get_goods_info().encode('utf-8'), clientAddr)
                elif userID in shops:
                    fromClient.sendto(shops[userID].goods.get_goods_info().encode('utf-8'), clientAddr)
                else:
                    fromClient.sendto(M3.get.encode('utf-8'), clientAddr) # 非商户在未进店时使用了/goods
                    
        elif request == "/customers":
            userID = has_logged_in(clientAddr)
            if userID == '':
                fromClient.sendto(M1.encode('utf-8'), clientAddr) # 未登录
                continue  
            if userID in behaviors:
                shopname = behaviors[userID].get_position()
                if shopname != '':
                    fromClient.sendto(shops[shopname].get_customer_list().encode('utf-8'), clientAddr)
                elif userID in shops:
                    fromClient.sendto(shops[userID].get_customer_list().encode('utf-8'), clientAddr)
                else:
                    fromClient.sendto(M3.get.encode('utf-8'), clientAddr) # 非商户在未进店时使用了/customers
        
        elif request.find("/buy") == 0:
            userID = has_logged_in(clientAddr)
            if userID == '':
                fromClient.sendto(M1.encode('utf-8'), clientAddr) # 未登录
            if userID in behaviors and behaviors[userID].get_position() != '':
                shopname = behaviors[userID].get_position()
                goodsID = request[5:]
                if shops[shopname].goods.has_good(goodsID):
                    fromClient.sendto(M0.encode('utf-8'), clientAddr)
                    fromClient.sendto((users[userID] + " has bought your product " + goodsID).encode('utf-8'), usersAddr[shopname])
                else:
                    fromClient.sendto(M5.encode('utf-8'), clientAddr)
        
        elif request == "/leave":
            userID = has_logged_in(clientAddr)
            if userID == '':
                fromClient.sendto(M1.encode('utf-8'), clientAddr) # 未登录
                continue
            if userID in behaviors and behaviors[userID].get_position() != '':
                fromClient.sendto(M0.encode('utf-8'), clientAddr) # 成功
                shopname = behaviors[userID].get_position()
                shops[shopname].customer_leave(userID)
                behaviors[userID].leave_shop()
                # 向商店老板发消息
                message = users[userID] + " has left your shop."
                fromClient.sendto(message.encode('utf-8'), usersAddr[shopname])
                
        # /addgoods goodsID goodsName goodsPrice
        elif request.find("/addgoods") == 0:
            if request[10:] != "":
                goods = request[10:].split()
                if len(goods) != 3:
                    fromClient.sendto(M5.encode('utf-8'), clientAddr) # 命令格式错误
                    continue
            userID = has_logged_in(clientAddr)
            if userID == '':
                fromClient.sendto(M1.encode('utf-8'), clientAddr) # 未登录
                continue
            if userID in shops:
                shops[userID].goods.add_goods(goods[0], goods[1], goods[2])
                fromClient.sendto(M0.encode('utf-8'), clientAddr)
                # 给每位正在逛的顾客发消息
                for customer in shops[userID].get_customerID_list():
                    fromClient.sendto("The shop has new product.".encode('utf-8'), usersAddr[customer])
            else:
                fromClient.sendto(M7.encode('utf-8'), clientAddr)
                
        else:
            fromClient.sendto(M5.encode('utf-8'), clientAddr)

# ----------------------------- 开启两个线程 -----------------------------

# 等待连接    
Host = ''
myPort = 50007

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as fromClient:
    
    fromClient.bind((Host, myPort))
    
    t1 = threading.Thread(target=administrator,  args = (fromClient, ))
    t2 = threading.Thread(target=client, args = (fromClient, ))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()