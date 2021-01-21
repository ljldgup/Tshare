# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 09:46:47 2018

@author: jialianl
"""

import pandas as pd
from sqlalchemy import create_engine
import time
import sys
import urllib.request

from tools.commom_tools import get_k_data

sys.path.append("..")
from HelloWorld import settings

# url = 'mysql+pymysql://ljl:123123@localhost:3306/django_test?charset=utf8'
# url= 'sqlite:///'+settings.DATABASES['default']['NAME']


if ('sqlite' in settings.DATABASES['default']['ENGINE']):
    url = 'sqlite:///' + settings.DATABASES['default']['NAME']
else:
    url = 'mysql+pymysql://' + settings.DATABASES['default']['USER'] + ':' + settings.DATABASES['default'][
        'PASSWORD'] + '@localhost:3306/' + settings.DATABASES['default']['NAME'] + '?charset=utf8'
yconnect = create_engine(url)


# delete k data
def user_proxy(proxy_addr):
    proxy = urllib.request.ProxyHandler({'http': proxy_addr})
    opener = urllib.request.build_opener(proxy, urllib.request.HTTPHandler)
    urllib.request.install_opener(opener)


def refresh_k_data(table, my_conn=yconnect):
    try:
        if ('sqlite' in settings.DATABASES['default']['ENGINE']):
            pd.read_sql_query('delete from ' + table + ';', con=my_conn)
            pd.read_sql_query('update sqlite_sequence SET seq = 0 where name = ' + table + ';', con=my_conn)
        else:
            pd.read_sql_query('truncate table ' + table + ';', con=my_conn)
    except BaseException as e:
        print(e)


# check if code's k data exists
def storekdata(code, my_conn=yconnect):
    data = pd.read_sql_query('select * from k_bfq where code = ' + code + ';', con=my_conn)

    if (len(data) == 0):
        data1 = get_k_data(code, k_type='bfq', t_type='d')
        data1['id'] = data1.index - data1.index.min()
        data1['code'] = code
        data1.to_sql('k_bfq', con=my_conn, if_exists='append')
        time.sleep(0.1)
    else:
        print(code + ':already in database')


if __name__ == '__main__':
    user_proxy("http://cn-proxy.jp.oracle.com:80")
    yconn = create_engine('sqlite:///db.sqlite3')
    storekdata('600859', yconn)
