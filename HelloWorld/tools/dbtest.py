# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 20:29:48 2018

@author: ljl
"""
from sqlalchemy import create_engine
import time
import sys

from tools.commom_tools import get_k_data

sys.path.append('../')
from HelloWorld import settings

if ('sqlite' in settings.DATABASES['default']['ENGINE']):
    url = 'sqlite:///' + settings.DATABASES['default']['NAME']
else:
    url = 'mysql+pymysql://' + settings.DATABASES['default']['USER'] + ':' + settings.DATABASES['default'][
        'PASSWORD'] + '@localhost:3306/' + settings.DATABASES['default']['NAME'] + '?charset=utf8'
yconnect = create_engine(url)


def store_k_data(code, yconnect):
    data1 = get_k_data(code, k_type='bfq', t_type='d')
    data1['id'] = data1.index - data1.index.min()
    data1['code'] = code
    data1.to_sql('k_bfq', con=yconnect, if_exists='replace')
    time.sleep(0.1)


# data2['id'] = data2.index.
# data2.to_sql("basic",con=yconnect,if_exists='replace')
if __name__ == '__main__':
    store_k_data('000001', yconnect)
