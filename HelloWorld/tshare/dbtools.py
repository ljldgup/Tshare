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
import urllib.request

sys.path.append("..")
from HelloWorld import settings

#url = 'mysql+pymysql://ljl:123123@localhost:3306/django_test?charset=utf8'
#url= 'sqlite:///'+settings.DATABASES['default']['NAME']


if('sqlite' in settings.DATABASES['default']['ENGINE']):
	url= 'sqlite:///'+settings.DATABASES['default']['NAME']
else:
	url = 'mysql+pymysql://ljl:123123@localhost:3306/django_test?charset=utf8'
yconnect = create_engine(url)

#delete k data
def user_proxy(proxy_addr):
    proxy = urllib.request.ProxyHandler({'http':proxy_addr})
    opener = urllib.request.build_opener(proxy, urllib.request.HTTPHandler)
    urllib.request.install_opener(opener)

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
	
    if (len(data) == 0):
        data1 = ts.get_k_data(code, ktype='D', autype=None ,index=False,start='2015-07-06', end=time.strftime('%Y-%m-%d',time.localtime(time.time())))
        data1['id'] = data1.index - data1.index.min()
        data1.to_sql('k_bfq', con=my_conn, if_exists='append')
        time.sleep(0.1)
    else:
        print(code + ':already in database')

if __name__ == '__main__':
    user_proxy("http://cn-proxy.jp.oracle.com:80")
    yconn = create_engine('sqlite:///db.sqlite3')
    storekdata('600859',yconn)
