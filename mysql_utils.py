#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import time
import re
import config
from DBUtils.PersistentDB import PersistentDB


class MysqlHelper(object):
    """MysqlHelper python class connects to MySQL. """

    _dbconfig = None
    _cursor = None
    _connect = None
    _error_code = '' # error_code from MySQLdb
    _pool = None

    TIMEOUT_DEADLINE = 30 # quit connect if beyond 30S
    TIMEOUT_THREAD = 10 # threadhold of one connect
    TIMEOUT_TOTAL = 0 # total time the connects have waste

    def __new__(cls, *args, **kw):
        '''
        单例实现
        :param args:
        :param kw:
        :return:
        '''
        if not hasattr(cls, '_instance'):
            orig = super(MysqlHelper, cls)
            cls._instance = orig.__new__(cls, *args, **kw)

            # 初始化数据库连接池
            cls._dbconfig = {'host': config.DB_HOST,
                             'port': config.DB_PORT,
                             'user': config.DB_USER,
                             'passwd': config.DB_PASSWD,
                             'db': config.DB_NAME,
                             'charset': config.DB_CHARSET}
            cls.dbconfig_test(cls._dbconfig)
            cls._pool = PersistentDB(
                creator=MySQLdb,
                maxusage=config.MAXUSAGE,
                host=cls._dbconfig['host'],
                port=cls._dbconfig['port'],
                user=cls._dbconfig['user'],
                passwd=cls._dbconfig['passwd'],
                db=cls._dbconfig['db'],
                charset=cls._dbconfig['charset'],
                connect_timeout=cls.TIMEOUT_THREAD)
        return cls._instance

    def __init__(self):
        try:
            self._connect = MysqlHelper._pool.connection(shareable=True)
            self._cursor = self._connect.cursor(MySQLdb.cursors.DictCursor)
            print '_pool id:', id(self._pool)
            print '_connect id:', id(self._connect)
        except MySQLdb.Error, e:
            self._error_code = e.args[0]
            error_msg = "%s --- %s" % (time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())), type(e).__name__), e.args[0], e.args[1]
            print error_msg
            raise Exception(error_msg)

    @classmethod
    def dbconfig_test(cls, dbconfig):
        flag = True
        if type(dbconfig) is not dict:
            print 'dbconfig is not dict'
            flag = False
        else:
            for key in ['host', 'port', 'user', 'passwd', 'db']:
                if not dbconfig.has_key(key):
                    print "dbconfig error: do not have %s" % key
                    flag = False
            if not dbconfig.has_key('charset'):
                cls._dbconfig['charset'] = 'utf8'

        if not flag:
            raise Exception('Dbconfig Error')
        return flag

    def query(self, sql, ret_type='all'):
        try:
            self._cursor.execute("SET NAMES utf8")
            self._cursor.execute(sql)
            if ret_type == 'all':
                return self.rows2array(self._cursor.fetchall())
            elif ret_type == 'one':
                return self._cursor.fetchone()
            elif ret_type == 'count':
                return self._cursor.rowcount
        except MySQLdb.Error, e:
            self._error_code = e.args[0]
            print "Mysql execute error:",e.args[0],e.args[1]
            return False

    def dml(self, sql):
        '''update or delete or insert'''
        try:
            self._cursor.execute("SET NAMES utf8")
            self._cursor.execute(sql)
            self._connect.commit()
            return True
        except MySQLdb.Error, e:
            self._error_code = e.args[0]
            print "Mysql execute error:",e.args[0],e.args[1]
            return False

    def dml_tran(self, sql_list):
        '''update or delete or insert with transaction'''
        try:
            self._cursor.execute("SET NAMES utf8")
            for sql in sql_list:
                self._cursor.execute(sql)
            self._connect.commit()
            return True
        except MySQLdb.Error, e:
            self._error_code = e.args[0]
            print "Mysql execute error:", e.args[0], e.args[1]
            self._connect.rollback()
            return False

    def dml_type(self, sql):
        re_dml = re.compile('^(?P<dml>\w+)\s+', re.I)
        m = re_dml.match(sql)
        if m:
            if m.group("dml").lower() == 'delete':
                return 'delete'
            elif m.group("dml").lower() == 'update':
                return 'update'
            elif m.group("dml").lower() == 'insert':
                return 'insert'
        print "%s --- Warning: '%s' is not dml." % (time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())), sql)
        return False


    def rows2array(self, data):
        '''transfer tuple to array.'''
        result = []
        for da in data:
            if type(da) is not dict:
                raise Exception('Format Error: data is not a dict.')
            result.append(da)
        return result

    def close(self):
        '''free source.'''
        try:
            self._cursor.close()
            self._connect.close()
        except:
            pass
