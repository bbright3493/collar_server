#! usr/bin/python
#coding=utf-8


'''
模块名称：
模块主要功能：
模块实现的方法：
模块对外接口：
模块作者：
编写时间：
修改说明：
修改时间：
'''
from __future__ import division
import re
import mysql_utils



#验证数据合法性   取出指令号  按照指令号调用不同的方法进行解析
class   dataParser(object):
    def __init__(self, data, ip):
        self.sourceDate = data
        self.imei = ''

        self.nav = 0
        self.speed = 0

        self.numsatellite = 0
        self.len_data = 0
        self.timedata = '201001010000'
        self.ip = ip
        self.Status_code = ''

        self.SleepCmd = 0x00 #ycq

        # 数据操作对象
        self.db = mysql_utils.MysqlHelper()

    def parserProcess(self):
        #判断数据的合法性
        if self.sourceDate[0]!=0x78 or self.sourceDate[1]!=0x78:
            return None
        else:
            self.len = self.sourceDate[2] #获取长度
            self.cmd = self.sourceDate[3]#获取指令号
            #根据指令号进行不同的协议处理
            if self.cmd == 0x01:
                return self.processLoginCmd()
            elif self.cmd == 0x08:
                return self.processHeartCmd()
            elif self.cmd == 0x10:
                return self.processGpsCmd()
            elif self.cmd == 0x13:
                return self.processStatusCmd()
            elif self.cmd == 0x14:
                return self.processSleepCmd()
            elif self.cmd == 0x17:
                return  self.processWifiCmd()
            elif self.cmd == 0x69:
                return self.processLBSCmd()


    def processLoginCmd(self):
        '''
        登录指令
        解析该指令
        获取imei
        判断ip是否有对应的imei
        没有则存储ip和imei到表ip_imei中
        返回回复内容
        '''
        self.login_data_len = self.sourceDate[2]
        for i in range(self.login_data_len - 4):
            self.imei += str(self.sourceDate[i + 4])

        #todo:根据imei查询ip
        # 根据imei查到对应的id和user_id
        db_ip = self.db.query("SELECT ip FROM collar_collar WHERE imei='%s'" % self.imei)

        device_type = 'N'

        if db_ip==[]:
            #查询不到则存储imei和ip
            print 'save imei and ip'
            sql = "INSERT INTO collar_collar(ip, imei, device_type) VALUES('%s', '%s', '%s')" % (self.ip, self.imei, device_type)
            self.db.dml(sql)
        elif db_ip[0]['ip']==self.ip:
            #同一个设备的ip发生了变化 更新ip
            sql = "UPDATE collar_collar SET ip='%s' WHERE imei='%s'" % (self.ip, self.imei)
            self.db.dml(sql)
        else:
            #没有变化 不做处理
            pass

        #todo：组装成返回的数据
        data = bytearray([0x78,0x78,0x01,0x01,0x0d,0x0a])
        strData = str(data)
        return strData

    def processHeartCmd(self):
        '''
        心跳指令
        可以不做任何处理
        '''
        pass

    def processGpsCmd(self):
        '''
        gps指令
        获取时间日期
        获取卫星个数
        获取并解析经纬度
        获取并解析速度
        获取并解析东西经南北纬 状态 航向
        根据ip地址查询imei号
        存储imei号 及 gps所有信息
        返回回复内容
        '''
        timedata = ''
        location_latitude = ''
        location_longitude = ''

        timeLists = self.sourceDate[4:10]

        #gps时间处理
        for timeList in timeLists:
            timedata = timedata + str(timeList)

        #组装成返回的字段
        retList = [0x78,0x78,0x06,0x10]
        retList.extend(timeLists)
        retList.extend([0x0d,0x0a])
        data = bytearray(retList)
        strData = str(data)

        #得到gps个数
        gpsNum = self.sourceDate[10] % 16

        #得到经度
        for i in range(11, 14 + 1):
            temp1 = str(hex(self.sourceDate[i]))
            temp2 = re.findall('0x([\dA-Fa-f]+)', temp1)
            temp2 = str(temp2[0])
            location_latitude += temp2
        location_latitude = '0x' + location_latitude
        location_latitude = int(location_latitude, 16)

        lat = location_latitude / 1800000
        print lat

        #得到纬度
        for i in range(15, 18 + 1):
            temp1 = str(hex(self.sourceDate[i]))
            temp2 = re.findall('0x([\dA-Fa-f]+)', temp1)
            temp2 = str(temp2[0])
            location_longitude += temp2
        location_longitude = '0x' + location_longitude
        location_longitude = int(location_longitude, 16)
        lng = location_longitude / 1800000
        print lng
        #得到速度
        gpsSpeed = self.sourceDate[19]

        #通过ip查询设备id和用户id
        collar = self.db.query("SELECT id,user_id FROM collar_collar WHERE ip='%s'" % self.ip)
        if collar:
            collar_id = collar[0]['id']
            user_id = collar[0]['user_id']
            localtype = 'G'

            print collar_id, user_id
            # 存储定位数据
            if user_id==None:
                sql = """
                        INSERT INTO collar_location(gps_time, loca_type, satellite, lat, lng, speed,
                        collar_id, add_time) VALUES('%s', '%s',
                        '%s', '%s', '%s', '%s', '%s', now())
                """ % (timedata, localtype, gpsNum, lat, lng, gpsSpeed, collar_id)
            else:
                sql = """
                        INSERT INTO collar_location(gps_time, loca_type, satellite, lat, lng, speed,
                        collar_id, user_id, add_time) VALUES('%s', '%s',
                        '%s', '%s', '%s', '%s', '%s','%s', now())
                """ % (timedata, localtype, gpsNum, lat, lng, gpsSpeed, collar_id, user_id)
            self.db.dml(sql)
        return strData

    def processStatusCmd(self):
        '''
        状态信息指令
        解析出电量和上传间隔
        并进行存储
        '''
        Status_code = ''
        for i in range(4, 9):
            Status_code += str(self.sourceDate[i])
        self.Status_code = Status_code

        #电池电量
        batPersent = self.sourceDate[4]
        #上传间隔
        timeGap = self.sourceDate[7]

        retList = [0x78,0x78,0x02,0x13,0x03,0x0d,0x0a]
        data = bytearray(retList)
        strData = str(data)

        # todo：通过ip地址查询到imei号
        # todo：将imei号和电池电量，上传间隔进行存储
        #通过ip查询设备id和用户id
        collar = self.db.query("SELECT id,user_id FROM collar_collar WHERE ip='%s'" % self.ip)
        if collar:
            collar_id = collar[0]['id']
            user_id = collar[0]['user_id']
            localtype = 'S'
            # 存储定位数据
            if user_id==None:
                sql = """
                        INSERT INTO collar_location(loca_type, bat_persent, upload_time,
                        collar_id, add_time) VALUES('%s', '%s',
                        '%s', '%s', now())
                """ % (localtype, batPersent, timeGap, collar_id)
            else:
                sql = """
                        INSERT INTO collar_location(loca_type, bat_persent, upload_time,
                        collar_id, user_id, add_time) VALUES('%s', '%s',
                        '%s', '%s', '%s', now())
                """ % (localtype, batPersent, timeGap, collar_id, user_id)
            self.db.dml(sql)

        return strData


    def processSleepCmd(self):
        '''
        设备通知休眠指令
        修改设备状态为休眠
        '''
        pass


    def processWifiCmd(self):
        '''
        0x17 离线wifi指令
        解析出wifi数量 数据日期 lbs数量 wifi数量 mcc mnc lac cellid msciss
        '''

        wifiData = []
        lbsData = []
        timedata = ''

        wifi_num = self.sourceDate[2]

        timeLists = self.sourceDate[4:10]

        for timeList in timeLists:
            timeList = hex(timeList)#转换成16进制显示
            timeList = str(timeList)#转换成字符
            timeList = timeList[2:4]
            timedata = timedata + str(timeList)


        retList = [0x78,0x78,0x00,0x69]
        retList.extend(timeLists)
        retList.extend([0x0d,0x0a])
        data = bytearray(retList)
        strData = str(data)

        if wifi_num>0:
            for i in range(0, 7*wifi_num):
                wifiData.append(self.sourceDate[10+i])

        print 'wifi数量: ', wifi_num
        print 'wifidata: ', wifiData

        if self.sourceDate[10+7*wifi_num]!=0x0d:
            lbs_num = self.sourceDate[10+7*wifi_num]
            print 'LBS数量: ', lbs_num
            lbs_start = 11+7*wifi_num
            for j in range(0, 3+5*lbs_num):
                lbsData.append(self.sourceDate[lbs_start+j])

        print '日期时间: ', timedata
        print 'lbsdaa ', lbsData
        # 返回结果

        #通过ip查询设备id和用户id
        collar = self.db.query("SELECT id,user_id FROM collar_collar WHERE ip='%s'" % self.ip)
        #对数据进行存储
        if collar:
            collar_id = collar[0]['id']
            user_id = collar[0]['user_id']
            localtype = 'F'
            print collar_id, user_id
            # 存储定位数据
            if user_id==None:
                sql = """
                        INSERT INTO collar_location(gps_time, loca_type, wifi_num,
                        wifi_data, lbs_num, lbs_data, collar_id, add_time) VALUES('%s', '%s',
                        '%s', '%s', '%s', '%s', '%s', now())
                """ % (timedata, localtype, wifi_num, wifiData, lbs_num, lbsData, collar_id)
            else:
                sql = """
                        INSERT INTO collar_location(gps_time, loca_type, wifi_num,
                        wifi_data, lbs_num, lbs_data, collar_id, user_id, add_time) VALUES('%s', '%s',
                        '%s', '%s', '%s', '%s', '%s', '%s', now())
                """ % (timedata, localtype, wifi_num, wifiData, lbs_num, lbsData, collar_id, user_id)
            self.db.dml(sql)

        return strData

    # 指令是0x69时的解析
    def processLBSCmd(self):
        '''
        0x17 离线wifi指令
        解析出wifi数量 数据日期 lbs数量 wifi数量 mcc mnc lac cellid msciss
        '''

        wifiData = []
        lbsData = []
        timedata = ''

        wifi_num = self.sourceDate[2]

        timeLists = self.sourceDate[4:10]
        #数据时间处理
        for timeList in timeLists:
            timeList = hex(timeList)#转换成16进制显示
            timeList = str(timeList)#转换成字符
            timeList = timeList[2:4]
            timedata = timedata + str(timeList)

        retList = [0x78,0x78,0x00,0x69]
        retList.extend(timeLists)
        retList.extend([0x0d,0x0a])
        data = bytearray(retList)
        strData = str(data)

        if wifi_num>0:
            for i in range(0, 7*wifi_num):
                wifiData.append(self.sourceDate[10+i])

        print 'wifi数量: ', wifi_num
        print 'wifidata: ', wifiData

        if self.sourceDate[10+7*wifi_num]!=0x0d:
            lbs_num = self.sourceDate[10+7*wifi_num]
            print 'LBS数量: ', lbs_num
            lbs_start = 11+7*wifi_num
            for j in range(0, 3+5*lbs_num):
                lbsData.append(self.sourceDate[lbs_start+j])

        print '日期时间: ', timedata
        print 'lbsdaa ', lbsData
        # 返回结果

        #通过ip查询设备id和用户id
        collar = self.db.query("SELECT id,user_id FROM collar_collar WHERE ip='%s'" % self.ip)
        #对数据进行存储
        if collar:
            collar_id = collar[0]['id']
            user_id = collar[0]['user_id']
            localtype = 'O'

            # 存储定位数据

            if user_id==None:
                sql = """
                        INSERT INTO collar_location(gps_time, loca_type, wifi_num,
                        wifi_data, lbs_num, lbs_data, collar_id, add_time) VALUES('%s', '%s',
                        '%s', '%s', '%s', '%s', '%s', now())
                """ % (timedata, localtype, wifi_num, wifiData, lbs_num, lbsData, collar_id)
            else:
                sql = """
                        INSERT INTO collar_location(gps_time, loca_type, wifi_num,
                        wifi_data, lbs_num, lbs_data, collar_id, user_id, add_time) VALUES('%s', '%s',
                        '%s', '%s', '%s', '%s', '%s', '%s', now())
                """ % (timedata, localtype, wifi_num, wifiData, lbs_num, lbsData, collar_id, user_id)

            self.db.dml(sql)

        return strData

