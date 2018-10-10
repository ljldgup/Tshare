# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 09:46:47 2018

@author: jialianl
"""

import pandas as pd
from sqlalchemy import create_engine
import tushare as ts
import time

def storekdata(code,my_conn):
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
    url = 'sqlite:///D:\work\DjangoTest\DjangoTest\HelloWorld\db.sqlite3'
    yconnect = create_engine(url)
    storekdata('600125',yconnect)
