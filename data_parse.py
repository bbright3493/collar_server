#! usr/bin/python
#coding=utf-8
import re

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

#验证数据合法性   取出指令号  按照指令号调用不同的方法进行解析


class   dataParser(object):
    def __init__(self, data):
        self.sourceDate = data
        self.login_data = ''

        self.nav = 0
        self.speed = 0
        self.location_latitude_reg = ''
        self.location_latitude_mint = ''
        self.location_longitude_reg = ''
        self.location_longitude_mint = ''
        self.numsatellite = 0
        self.len_data = 0
        self.timedata = '201001010000'
        self.GpsData = []

        self.Status_code = ''

        self.SleepCmd = 0x00 #ycq



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
        self.login_data_len = self.sourceDate[2]
        for i in range(self.login_data_len - 4):
            self.login_data += str(self.sourceDate[i + 4])
        #todo：判断ip地址是否发生变化 变化则重新存储ip
        #todo：存储imei和ip
        #todo：组装成返回的数据
        return self.login_data

    def processHeartCmd(self):
        return self.cmd

    def processGpsCmd(self):
        timedata = ''
        location_latitude = ''
        location_longitude = ''
        temp1 = ''
        temp2 = ''
        for i in range(4, 9+1):
            timedata += str(hex(self.sourceDate[i]))

        #todo：存储时间数据
        #组装成返回的字段
        self.timedata = '0x780x780x06x10' + timedata + '0x0d0x0a'


        for i in range(11, 14 + 1):
            temp1 = str(hex(self.sourceDate[i]))
            temp2 = re.findall('0x([\dA-Fa-f]+)', temp1)
            temp2 = str(temp2[0])
            location_latitude += temp2
        location_latitude = '0x' + location_latitude
        location_latitude = int(location_latitude, 16)
        self.location_latitude_reg = str(int(location_latitude) // 1800000) + '.' + str(int((location_latitude % 1800000 / 60) * 100))
        self.location_latitude_mint = str(location_latitude % 1800000)


        for i in range(15, 18 + 1):
            temp1 = str(hex(self.sourceDate[i]))
            temp2 = re.findall('0x([\dA-Fa-f]+)', temp1)
            temp2 = str(temp2[0])
            location_longitude += temp2
        location_longitude = '0x' + location_longitude
        location_longitude = int(location_longitude, 16)
        self.location_longitude_reg = str(int(location_longitude) // 1800000) + '.' + str(int((location_longitude % 1800000 / 60) * 100))
        self.location_longitude_mint = str(location_longitude % 1800000)
        self.GpsData = [self.timedata, self.location_latitude_reg, self.location_latitude_mint,self.location_longitude_reg,self.location_longitude_mint]


        #todo：通过ip地址查询到imei号
        #todo：将imei号和gps定位数据进行存储


        return self.GpsData

    def processStatusCmd(self):
        Status_code = ''
        for i in range(4, 9):
            Status_code += str(self.sourceDate[i])
        self.Status_code = Status_code

        # todo：通过ip地址查询到imei号
        # todo：将imei号和状态数据进行存储

        return self.Status_code

        # 指令号是0x14时的解析
    # LBS个数：05 为基站数量，基站数量最小为2个
    # MCCMNC：mcc2byte，mnc1byte 01CC00为46000
    def processSleepCmd(self):
        result = self.get_instruction(self.sourceDate)
        print '设备休眠: ', result
        # todo：通过ip地址查询到imei号
        # todo：将imei号和休眠状态进行存储

        return None

    # 指令是0x17时的解析
    def processWifiCmd(self):
        result = self.get_instruction(self.sourceDate)
        # wifi数量
        wifi_num = result[4:6]
        # 日期时间
        data_time = result[8:20]
        time = '%s-%s-%s %s:%s:%s' % (data_time[0:2], data_time[2:4], data_time[4:6],
                                      data_time[6:8], data_time[8:10], data_time[10:12])
        # LBS数量
        LBS_num = result[20:22]
        # MCCMNC
        MCCMNC = int(str(result[22:28]).replace('00',''),16)
        # lac celid msciss
        LBS_data = result[28:-4]
        lac_cellid_mciss = self.lbs_lac(LBS_data)
        print 'wifi数量: ', wifi_num
        print '日期时间: ', time
        print 'LBS数量: ', LBS_num
        print 'MCCMNC: ', MCCMNC
        print 'lac-celid-mciss: ', lac_cellid_mciss
        # 返回结果
        #todo 根据ip地址找到imei号
        #todo 保存imei，wifi数据和lbs数据
        return self._send_data(result)

    # 指令是0x69时的解析
    def processLBSCmd(self):
        result = self.get_instruction(self.sourceDate)
        # wifi数量
        wifi_num = result[4:6]
        # 日期时间
        data_time = result[8:20]
        time = '%s-%s-%s %s:%s:%s' % (data_time[0:2], data_time[2:4], data_time[4:6],
                                      data_time[6:8], data_time[8:10], data_time[10:12])
        # wifi数据
        wifi_bssid_rssi = {} # wifi数据信息
        if wifi_num != '00':
            result1 = result
            wifi_data = result1[20:(20+14*int(wifi_num))]
            # 获取wifi信号组
            i = 0
            data_list = []
            while i < len(wifi_data):
                data_list.append(wifi_data[i:i+14])
                i += 14
                # wifi信号解析
            for i in data_list:
                i1 = '0x'+ i[0:2] + ':0x' + i[2:4] + ':0x' + i[4:6] + ':0x' + i[6:8] + ':0x' + i[8:10] + ':0x' + i[10:12] + ':0x' + i[12:14]
                wifi_bssid_rssi[i1[0:29]] = i1[30:]
                # LBS个数
            LBS_num = result1[(20+14*int(wifi_num)):(22+14*int(wifi_num))]
            # MCCMNC
            MCCMNC1 = result1[(22+14*int(wifi_num)):(26+14*int(wifi_num))]
            MCCMNC = int(MCCMNC1, 16)
            # lac_cellid_mciss
            LBS_data = result1[(28+14*int(wifi_num)):-4]
            lac_cellid_mciss = self.lbs_lac(LBS_data)
        else:
            result1 = result
            # wifi信号
            wifi_bssid_rssi = {}
            # LBS个数
            LBS_num = result1[20:22]
            # MCCMNC
            MCCMNC1 = int(str(result[22:28]).replace('00',''),16)
            # lac_cellid_mciss
            LBS_data = result[28:-4]
            lac_cellid_mciss = self.lbs_lac(LBS_data)
            print 'wifi数量: ', wifi_num
            print 'wifi数据：', wifi_bssid_rssi
            print '日期时间: ', time
            print 'LBS数量: ', LBS_num
            print 'MCCMNC: ', MCCMNC1
            print 'lac-celid-mciss: ', lac_cellid_mciss
            #todo：根据ip查询imei
            #todo：保存imei，wifi数据和lbs数据

        return self._send_data(result)


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

    # 将指令转换为7878...格式
    def get_instruction(self, content):
        list = []
        for i in self.sourceDate:
            demo = self.dec2hex(str(i))
            demo = re.match('00(.*)', demo)
            list.append(demo.group(1))
        result = ''.join(list)
        return result


    # 返回的指令，格式为 7878+0x+协议号+时间+结尾2byte，格式为字符串
    def _send_data(self, content):
        result = content[0:20] + content[-4:]
        return result

    # 转换lac_ss格式
    def lbs_lac(self,LBS_data):
        i = 0
        LBS_data_list = []
        lac_cellid_mciss = {}
        while i < len(LBS_data):
            LBS_data_list.append(LBS_data[i:i + 10])
            i += 10
        j = 0
        for data in LBS_data_list:
            lac_cellid_mciss[j+1] = '%s_%s_%s' % (int(str(data[0:4]), 16),
                                                  int(str(data[4:8]), 16),
                                                  int(str(data[8:10]), 16))
            j += 1
        return lac_cellid_mciss
