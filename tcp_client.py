#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: yopoing
# date: 2017/3/5

from socket import *

HOST = 'localhost'
PORT = 9999
BUFSIZ = 1024
ADDR = (HOST, PORT)
tcpCliSock = socket(AF_INET, SOCK_STREAM)
tcpCliSock.connect(ADDR)
# data = 'S168#861118010019063#043b#0006#SYNC:0$'
data = 'S168#861118010019063#002a#00af#LOCA:G;CELL:6,1cc,0,8109,ad2d,1a,8109,ad2c,23,8109,ad2f,1b,8109,ad30,19,8109,ad2b,10,8109,ad2e,d;GDATA:A,3,170329095506,30.551296,104.087959,10,27,449;ALERT:0000;STATUS:72,100$'
tcpCliSock.send(data)
data1 = tcpCliSock.recv(BUFSIZ)
print data1
tcpCliSock.close()