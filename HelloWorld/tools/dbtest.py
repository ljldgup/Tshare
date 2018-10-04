# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 20:29:48 2018

@author: ljl
"""
import trade_analysis as tr_ansys
from sqlalchemy import create_engine
import tushare as ts
import pandas as pd

yconnect = create_engine('mysql+pymysql://ljl:123123@localhost:3306/django_test?charset=utf8')

data1=ts.get_k_data('002242', ktype='W', autype='qfq' ,index=False,start='2015-07-06', end='2017-11-09')

data1.to_sql("k_qfq_002242",con=yconnect,if_exists='append')