#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: yopoing
# date: 2017/3/5

import threading
import SocketServer
#import mysql_utils
import config
import time
import data_tool
import binascii
import data_parse
import time



lastip = 0

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    """
    请求处理的handler
    """

    def handle(self):
        global lastip
        print time.ctime(), '...connected from:', self.client_address
        while True:
            data = self.request.recv(config.BUFFER_SIZE)
            if not data:
                print time.ctime(), self.client_address, '(server)client quit'
                break
            else:
                if 'x'==data[0]:
                    print time.ctime(), self.client_address, 'client: ', binascii.b2a_hex(data)
                    dataArray = bytearray(data)
                    dataParser = data_parse.dataParser(dataArray, self.client_address[0])
                    result = dataParser.parserProcess()
                    print result
                    self.request.sendall('%s' % result)
                else:
                    print time.ctime(), self.client_address, 'client: ', data
                    analysis = data_tool.Analysis(data)
                    # 检查数据格式是否正确, 如果不正确则直接抛弃
                    if not analysis.check():
                        continue
                    # 修改时间间隔
                    result = analysis.change_time()
                    if result is None:
                        if analysis.type == 'SYNC':
                            result = analysis.heartbeat_packets()
                        elif analysis.type == 'LOCA':
                            result = analysis.location_packets()
                        elif analysis.type == 'B2G':
                            result = analysis.agps_packets()
                    self.request.sendall('%s' % result)



class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """
    多线程处理的TCP服务器
    """
    # 允许重用地址
    allow_reuse_address = True


if __name__ == '__main__':
    server = ThreadedTCPServer(
        (config.SERVER_HOST,
         config.SERVER_PORT),
        ThreadedTCPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    print 'Bind TCP on 9999...'
