import json
import os
import sys
from datetime import datetime
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import tushare as ts
import urllib.request

'''
fields1是data下的数据属性，fields2是klines中的具体数据类型
fqt 0不复权,1前复权，2后复权， 
klt=101 日线 102周线 103月线线
secid 深市0，沪市1，如secid=1.600016 secid=0.002583 secid=0.300124
'''
EAST_MONEY_URL = 'http://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f61&beg=0&end=20500101&rtntype=6&secid={}.{}&klt={}&fqt={}'
# turnover成交额， turnover_rate换手率
EAST_MONEY_COLUMNS = ['date', 'open', 'close', 'high', 'low', 'volume', 'turnover', 'amplitude ', 'pct_chg',
                      'turnover_rate']


def use_proxy():
    HTTP_PROXY = "http_proxy"
    HTTPS_PROXY = "https_proxy"
    os.environ[HTTP_PROXY] = "cn-proxy.jp.oracle.com:80"
    os.environ[HTTPS_PROXY] = "cn-proxy.jp.oracle.com:80"
    print(os.environ["http_proxy"])
    print(os.environ["https_proxy"])


# 不复权，或者指数使用tshare，否则使用洞房财富
# 全部用东方财富
def get_k_data(code, k_type='bfq'):
    # if k_type == 'bfq' or code == 'sh' or code == 'sz' or code == 'cyb':
    #    return get_and_cache_with_tushare(code)
    # else:
    return get_and_cache_with_dfcf(code, k_type)


# tushare获取主要用于不复权数据
def get_and_cache_with_tushare(code):
    # 获取，并缓存
    if not os.path.exists('data'):
        os.mkdir('data')
    today = datetime.now().strftime(("%Y-%m-%d"))
    today_folder = "data\\" + today
    if not os.path.exists(today_folder):
        os.mkdir(today_folder)
    if os.path.exists(today_folder + '\\' + code + '_0_d') and \
            os.path.exists(today_folder + '\\' + code + '_0_w') and \
            os.path.exists(today_folder + '\\' + code + '_0_m'):
        print("read from csv")
        ori_data_d = pd.read_csv(today_folder + '\\' + code + '_0_d')
        ori_data_w = pd.read_csv(today_folder + '\\' + code + '_0_w')
        ori_data_m = pd.read_csv(today_folder + '\\' + code + '_0_m')

    else:
        ori_data_m = ts.get_k_data(code, ktype='M', autype='bfq', index=False,
                                   start='2001-01-01', end=today)
        sleep(0.3)
        ori_data_w = ts.get_k_data(code, ktype='W', autype='bfq', index=False,
                                   start='2001-01-01', end=today)
        sleep(0.3)
        ori_data_d = ts.get_k_data(code, ktype='D', autype='bfq', index=False,
                                   start='2001-01-01', end=today)
        sleep(0.3)
        if len(ori_data_m) > 10:
            ori_data_d.to_csv(today_folder + '\\' + code + '_0_d')
            ori_data_w.to_csv(today_folder + '\\' + code + '_0_w')
            ori_data_m.to_csv(today_folder + '\\' + code + '_0_m')

    for data in [ori_data_m, ori_data_w, ori_data_d]:
        data['pct_chg'] = data['close'].pct_change().fillna(0).map(two_digit_percent)
    return [ori_data_d, ori_data_w, ori_data_m]


# 两位小数百分比
def two_digit_percent(number):
    return round(number, 4) * 100


# 东方财富主要用于复权数据，tushare复权数据有问题
def get_and_cache_with_dfcf(code: str, k_type: str):
    if not os.path.exists('data'):
        os.mkdir('data')
    today = datetime.now().strftime(("%Y-%m-%d"))
    today_folder = "data\\" + today
    if not os.path.exists(today_folder):
        os.mkdir(today_folder)
    if os.path.exists(today_folder + '\\' + code + '_1_d' + k_type) and \
            os.path.exists(today_folder + '\\' + code + '_1_w' + k_type) and \
            os.path.exists(today_folder + '\\' + code + '_1_m' + k_type):
        print("read from csv")
        ori_data_d = pd.read_csv(today_folder + '\\' + code + '_1_d' + k_type)
        ori_data_w = pd.read_csv(today_folder + '\\' + code + '_1_w' + k_type)
        ori_data_m = pd.read_csv(today_folder + '\\' + code + '_1_m' + k_type)
        ans = [ori_data_d, ori_data_w, ori_data_m]

    else:
        ans = []
        if code == 'sh':
            sect_id = 1
            code = '000001'
        elif code == 'sz':
            sect_id = 0
            code = '399001'
        elif code == 'cyb':
            sect_id = 0
            code = '399006'
        elif code.startswith('600'):
            sect_id = 1
        else:
            sect_id = 0
        # 默认前复权
        fqt = {'bfq': 0, 'qfq': 1, 'hfq': 2}[k_type]
        for klt in [101, 102, 103]:
            url = EAST_MONEY_URL.format(sect_id, code, klt, fqt)
            with urllib.request.urlopen(url) as req:
                # 返回的是多重嵌套字典
                json_data = json.load(req)
            k_lines_data = [data.split(',') for data in json_data['data']['klines']]
            data = pd.DataFrame(k_lines_data, columns=EAST_MONEY_COLUMNS)
            data[EAST_MONEY_COLUMNS[1:]] = data[EAST_MONEY_COLUMNS[1:]].astype(float)
            ans.append(data)

            sleep(0.5)

        ans[0].to_csv(today_folder + '\\' + code + '_1_d' + k_type)
        ans[1].to_csv(today_folder + '\\' + code + '_1_w' + k_type)
        ans[2].to_csv(today_folder + '\\' + code + '_1_m' + k_type)

    return ans


if __name__ == '__main__':
    t = get_and_cache_with_dfcf('sh', 'qfq')
    t = get_and_cache_with_dfcf('600016', 'qfq')
    t = get_and_cache_with_dfcf('600016', 'bfq')