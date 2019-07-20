# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 20:29:48 2018

@author: ljl
"""
from sqlalchemy import create_engine
import tushare as ts
import time
import sys

sys.path.append('../')
from HelloWorld import settings

if('sqlite' in settings.DATABASES['default']['ENGINE']):
    url= 'sqlite:///' + settings.DATABASES['default']['NAME']
else:
    url = 'mysql+pymysql://' + settings.DATABASES['default']['USER'] + ':' + settings.DATABASES['default']['PASSWORD'] + '@localhost:3306/' + settings.DATABASES['default']['NAME'] + '?charset=utf8'
yconnect = create_engine(url)

def storekdata(code,yconnect):

    data1 = ts.get_k_data(code, ktype='D', autype=None ,index=False,start='2015-07-06', end='2018-09-28')
    data1['id'] = data1.index - data1.index.min()
    data1.to_sql('k_bfq',con=yconnect,if_exists='replace')
    time.sleep(0.1)
#data2['id'] = data2.index.
#data2.to_sql("basic",con=yconnect,if_exists='replace')
if __name__ == '__main__':
    storekdata('000001',yconnect)