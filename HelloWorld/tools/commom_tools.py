"""
后端拉取数据
"""
import json
import os
from datetime import datetime
import time

import pandas as pd

import urllib.request

'''
fields1是data下的数据属性，fields2是klines中的具体数据类型
fqt 0不复权,1前复权，2后复权， 
klt=101 日线 102周线 103月线线
secid 深市0，沪市1，如secid=1.600016 secid=0.002583 secid=0.300124
'''
EAST_MONEY_URL = 'http://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f61&beg=0&end=20500101&rtntype=6&secid={}.{}&klt={}&fqt={}'
# turnover成交额， turnover_rate换手率
EAST_MONEY_COLUMNS = ['date', 'open', 'close', 'high', 'low', 'volume', 'turnover', 'amplitude ', 'pct',
                      'turnover_rate']
# 指数拼音映射到接口代码
INDEX_CODE_MAP = {'sh': '000001', 'sz': '399001', 'cyb': '399006'}
CODE_SECT_ID_MAP = {'sh': 1, '000001': 1, '399006': 1}
FUQUAN_TYPE_MAP = {'bfq': 0, 'qfq': 1, 'hfq': 2}
PERIOD_TYPE_MAP = {'d': 101, 'w': 102, 'm': 103}

'''
财务数据 type 0 按报告期， 1 年度， 2 按单季度
'''
EAST_MONEY_FINICAL_URL = 'http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type={}&code={}&beg=0&end=20500101'

def use_proxy():
    HTTP_PROXY = "http_proxy"
    HTTPS_PROXY = "https_proxy"
    os.environ[HTTP_PROXY] = "cn-proxy.jp.oracle.com:80"
    os.environ[HTTPS_PROXY] = "cn-proxy.jp.oracle.com:80"
    print(os.environ["http_proxy"])
    print(os.environ["https_proxy"])


def get_code_and_sect_id(code):
    result = []
    # code
    if code in INDEX_CODE_MAP:
        result.append(INDEX_CODE_MAP[code])
    else:
        result.append(code)

    # sect_id
    if code in CODE_SECT_ID_MAP:
        result.append(CODE_SECT_ID_MAP[code])
    elif code.startswith('6'):
        result.append(1)
    else:
        result.append(0)

    return result


# 不复权，或者指数使用tshare，否则使用洞房财富
# 全部用东方财富
def get_k_data(code, t_type, k_type):
    # if k_type == 'bfq' or code == 'sh' or code == 'sz' or code == 'cyb':
    #    return get_and_cache_with_tushare(code)
    # else:
    return get_and_cache_with_dfcf(code, t_type, k_type)


# 两位小数百分比
def two_digit_percent(number):
    return round(number, 4) * 100


# 东方财富主要用于复权数据，tushare复权数据有问题
def get_and_cache_with_dfcf(code: str, t_type: str, k_type: str):

    code, sect_id = get_code_and_sect_id(code)
    if not os.path.exists('cached_data'):
        os.mkdir('cached_data')

    if not os.path.exists('cached_data/'):
        os.mkdir('cached_data/')

    cache_folder = 'cached_data/' + datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(cache_folder):
        os.mkdir(cache_folder)

    if os.path.exists('{}/{}_{}_{}'.format(cache_folder, code, t_type, k_type)):
        print("read from csv")
        return pd.read_csv('{}/{}_{}_{}'.format(cache_folder, code, t_type, k_type))

    # 接口参数到东方财富的适配
    # 默认前复权
    fqt = FUQUAN_TYPE_MAP[k_type]
    klt = PERIOD_TYPE_MAP[t_type]
    url = EAST_MONEY_URL.format(sect_id, code, klt, fqt)
    with urllib.request.urlopen(url) as req:
        # 返回的是多重嵌套字典
        print(url)
        json_data = json.load(req)
    k_lines_data = [data.split(',') for data in json_data['data']['klines']]
    data = pd.DataFrame(k_lines_data, columns=EAST_MONEY_COLUMNS)
    data['code'] = code
    data[EAST_MONEY_COLUMNS[1:]] = data[EAST_MONEY_COLUMNS[1:]].astype(float)
    data.to_csv('{}/{}_{}_{}'.format(cache_folder, code, t_type, k_type))

    return data


if __name__ == '__main__':
    with open('codes.json') as f:
        codes = json.load(f)
    for t in ['d', 'w', 'm']:
        for code in codes['codes']:
            get_and_cache_with_dfcf(code, t, 'qfq')
            time.sleep(1)
