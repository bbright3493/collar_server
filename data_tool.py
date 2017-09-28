#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: yopoing
# date: 2017/3/7

import datetime
import mysql_utils


class Analysis(object):

    """
    数据通用解析类
    """

    def __init__(self, data):
        # 接收到的原始数据，去掉$符号并转换为数组
        self.source_data = data.strip()
        if self.check():
            self.data = self.source_data.replace('$','').split('#')
            # ID号
            self.id = self.data[0]
            # IMEI号码
            self.imei = self.data[1]
            # 流水号
            self.seq_no = self.data[2]
            # 长度
            self.len = self.data[3]
            # 类型
            self.type = self.data[4][:self.data[4].find(':')]
            # 内容
            self.content = self.data[4][self.data[4].find(':')+1:]
            # 数据操作对象
            self.db = mysql_utils.MysqlHelper()
            print '---------------------------'
            print '__init__'
            print 'ID号:', self.id
            print 'IMEI:', self.imei
            print '流水号:', self.seq_no
            print '长度:', self.len
            print '协议类型:', self.type
            print '内容', self.content
            print '---------------------------'

    def heartbeat_packets(self):

        """
        心跳包
        :return:
        """

        # 对解析到的内容具体进行处理
        print '---------------------------'
        print 'heartbeat_packets'
        print '具体内容:', self.content
        print '---------------------------'
        # 存储数据
        # 判断是否已经有该IMEI的设备，无则添加设备
        imei_count = self.db.query("SELECT COUNT(imei) as imei_count FROM collar_collar "
                                   "WHERE imei='%s'" % self.imei)[0]['imei_count']
        if imei_count == 0:
            self.db.dml("INSERT INTO collar_collar(imei, bind_time, add_time) VALUES('%s', now(), now())" % self.imei)
        # 返回要发回的数据
        content = 'ACK^SYNC,%s' % datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return self.get_callback(content)

    def location_packets(self):

        """
        定位数据包
        :return:
        """

        # 对解析到的内容具体进行处理
        print '---------------------------'
        print 'location_packets'
        print '具体内容:', self.content

        """
        L;CELL:5,1cc,0,8109,8536,12,8109,5fc9,16,8109,dd6,e,8109,8535,e,8109,dd7,c;GDATA:V,0,170308084536,0.000000,0.000000,0,0,0;ALERT:0000;STATUS:93,70
        基站个数可能有多个，我的理解应该是拿信号最好的那个来作为最佳的定位位置。
        """

        # 按照;来拆分接收到的内容
        self.content = self.content.split(';')
        # 定位类型
        loca_type = self.content[0]

        # 基站信息
        cell = self.content[1].split(':')[1]
        # gps信息
        gdata = self.content[2].split(':')[1].split(',')
        # 是否定位(A定位，V未定位)
        is_loca = gdata[0]
        # 卫星个数
        satellite = gdata[1]
        # gps时间
        gps_time = gdata[2]
        # 纬度
        lat = gdata[3]
        # 经度
        lng = gdata[4]
        # 速度
        speed = gdata[5]
        # 航向
        direction = gdata[6]
        # 海拔
        altitude = gdata[7]

        # alert信息
        alert = self.content[3].split(':')[1]
        # 状态信息
        status = self.content[4].split(':')[1]

        # 根据imei查到对应的id和user_id
        collar = self.db.query("SELECT id,user_id FROM collar_collar WHERE imei='%s'" % self.imei)
        if collar:
            collar_id = collar[0]['id']
            user_id = collar[0]['user_id']
            # 存储定位数据
            sql = """
                  INSERT INTO collar_location(loca_type, cell, is_loca, satellite, gps_time,
                  lat, lng, speed, direction, altitude, alert, status, collar_id, user_id, add_time) VALUES('%s', '%s', '%s', '%s', '%s',
                  '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s, now())
            """ % (loca_type, cell, is_loca, satellite, gps_time,lat, lng, speed,
                   direction, altitude, alert, status, collar_id, user_id)
            self.db.dml(sql)

            # 存储历史定位数据
            sql = """
                              INSERT INTO collar_locationhistory(loca_type, cell, is_loca, satellite, gps_time,
                              lat, lng, speed, direction, altitude, alert, status, collar_id, user_id, add_time) VALUES('%s', '%s', '%s', '%s', '%s',
                              '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s, now())
                        """ % (loca_type, cell, is_loca, satellite, gps_time, lat, lng, speed,
                               direction, altitude, alert, status, collar_id, user_id)
            self.db.dml(sql)

        print '定位类型:', loca_type
        print '基站信息:', cell
        print 'gps信息:', gdata
        print '是否定位:', is_loca
        print '卫星个数:', satellite
        print 'gps时间:', gps_time
        print '纬度:', lat
        print '经度:', lng
        print '速度:', speed
        print '航向:', direction
        print '海拔:', altitude
        print '报警信息:', alert
        print '状态信息:', status

        print '---------------------------'


        content = 'ACK^LOCA'
        return self.get_callback(content)

    def agps_packets(self):

        """
        apps命令包
        :return:
        """
        # 对解析到的内容具体进行处理
        print '---------------------------'
        print 'agps_packets'
        print '具体内容:', self.content
        print '---------------------------'

        content = 'ACK^B2G,38.65777,104.08296'
        return self.get_callback(content)

    def change_time(self):
        """
        修改时间间隔
        :return:
        """
        # 根据imei查询项圈的时间间隔和标识
        collar = self.db.query("SELECT time_interval,time_interval_flag FROM collar_collar WHERE imei='%s'" % self.imei)
        if collar:
            time_interval = collar[0]['time_interval']
            time_interval_flag = collar[0]['time_interval_flag']
            if not time_interval_flag:
                sql = "UPDATE collar_collar SET time_interval_flag=True WHERE imei='%s'" % self.imei
                self.db.dml(sql)
                return self.get_callback("UP,%s" % time_interval)
        return None


    def get_callback(self, content):

        """
        得到要返回的数据
        :param content:
        :return:
        """

        result = '%s#%s#%s#%s#%s' % (self.id, self.imei, self.seq_no, Analysis.dec2hex(len(content)), content)
        print '---------------------------'
        print 'get_callback'
        print '回复的内容:', result
        print '---------------------------'
        return result

    def check(self):

        """
        检查数据合法性，没有#或者$肯定为不合法数据
        :param data:
        :return:
        """

        if self.source_data.find('#') == -1 or self.source_data.find('$') == -1:
            return False
        return True

    @staticmethod
    def dec2hex(string_num):

        """
        十进制转十六进制
        :return:
        """

        base = [str(x) for x in range(10)] + [chr(x) for x in range(ord('A'), ord('A') + 6)]
        num = int(string_num)
        mid = []
        while True:
            if num == 0: break
            num, rem = divmod(num, 16)
            mid.append(base[rem])
        mid = mid + ['0'] * (4 - len(mid)) if len(mid) < 4 else mid
        return ''.join([str(x) for x in mid[::-1]])