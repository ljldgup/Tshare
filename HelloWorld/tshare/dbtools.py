# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 09:46:47 2018

@author: jialianl
"""

import pandas as pd
from sqlalchemy import create_engine
import tushare as ts
import time
import sys
import os

sys.path.append("..")
from HelloWorld import settings

#url = 'mysql+pymysql://ljl:123123@localhost:3306/django_test?charset=utf8'
url= 'sqlite:///D:\work\DjangoTest\DjangoTest\HelloWorld\db.sqlite3'
yconnect = create_engine(url)


#delete k data
def refresh_k_data(table,my_conn = yconnect):
    try:
        if('sqlite' in settings.DATABASES['default']['ENGINE']):
            pd.read_sql_query('delete from ' + table + ';', con = my_conn)
            pd.read_sql_query('update sqlite_sequence SET seq = 0 where name = ' + table + ';', con = my_conn)
        else:
            pd.read_sql_query('truncate table ' + table + ';', con = my_conn)
    except BaseException as e:
        print(e)

#check if code's k data exists
def storekdata(code,my_conn = yconnect):
    data = pd.read_sql_query('select * from k_bfq where code = ' + code + ';', con = my_conn)
    print(len(data))
    if (len(data) == 0):
        print("??")
        data1 = ts.get_k_data(code, ktype='D', autype=None ,index=False,start='2015-07-06', end='2018-09-28')
        data1['id'] = data1.index - data1.index.min()
        data1.to_sql('k_bfq', con=my_conn, if_exists='append')
        time.sleep(0.1)
    else:
        print(code + ':already in database')

if __name__ == '__main__':
    HTTP_PROXY = "http_proxy"
    HTTPS_PROXY = "https_proxy"
    os.environ[HTTP_PROXY] = "cn-proxy.jp.oracle.com:80"
    os.environ[HTTPS_PROXY] = "cn-proxy.jp.oracle.com:80"
    print (os.environ["http_proxy"])
    print (os.environ["https_proxy"])
    refresh_k_data('k_bfq')
    storekdata('600125')
