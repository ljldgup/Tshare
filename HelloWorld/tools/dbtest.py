# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 20:29:48 2018

@author: ljl
"""
from sqlalchemy import create_engine
import tushare as ts
import time

yconnect = create_engine('mysql+pymysql://ljl:123123@localhost:3306/django_test?charset=utf8')

def storekdata(code):
   
    data1 = ts.get_k_data(code, ktype='D', autype=None ,index=False,start='2015-07-06', end='2018-09-28')
    data1['id'] = data1.index - data1.index.min()
    data1.to_sql('k_bfq',con=yconnect,if_exists='append')
    time.sleep(0.1)
#data2['id'] = data2.index.
#data2.to_sql("basic",con=yconnect,if_exists='replace')
if __name__ == '__main__':
    storekdata('600859')