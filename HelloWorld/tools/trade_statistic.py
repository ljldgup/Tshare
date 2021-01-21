# -*- coding: utf-8 -*-
"""
用于统计交易盈亏，频率等
"""
import os, sys

import pandas as pd
from sqlalchemy import create_engine

# tools 报错把 外层Helloworld 文件夹 右键 make directory as -> source root
from tools import dbtest
from tools.commom_tools import two_digit_percent

sys.path.append("..")
from HelloWorld import settings


def use_proxy():
    HTTP_PROXY = "http_proxy"
    HTTPS_PROXY = "https_proxy"
    os.environ[HTTP_PROXY] = "cn-proxy.jp.oracle.com:80"
    os.environ[HTTPS_PROXY] = "cn-proxy.jp.oracle.com:80"
    print(os.environ["http_proxy"])
    print(os.environ["https_proxy"])


# 补全股票代码
def code_complete(code):
    s_code = str(int(code))
    for i in range(6 - len(s_code)):
        s_code = '0' + s_code
    return s_code


# 每个股票的每次交易数据统计
def get_trade(data):
    index = -1

    trade_data = pd.DataFrame(columns=["code", "name", "i_date", "o_date", "i_total", "o_total", "amount"])

    for name in data["name"].drop_duplicates():
        t_count = 0
        getsum = 0
        getamount = 0
        for i in data[data["name"] == name].index:
            if data.at[i, 'amount'] < 0:
                getsum -= int(data.at[i, 'sum'])
            else:
                getsum += int(data.at[i, 'sum'])
            getamount += int(data.at[i, 'amount'])
            data.at[i, 'getamount'] = getamount

            # 手数为0后持仓就是亏损
            if getamount == 0:
                data.at[i, 'getsum'] = -getsum
                getsum = 0

            # 新的交易
            if t_count == 0:
                index += 1
                trade_data.loc[index] = [data.at[i, 'code'], name, data.at[i, 'date'], data.at[i, 'date'],
                                         int(data.at[i, 'sum']), 0, int(data.at[i, 'amount'])]
                t_count = data.at[i, 'amount']

            else:
                trade_data.at[index, "name"] = name

                if data.at[i, 'amount'] < 0:
                    trade_data.at[index, "o_total"] += int(data.at[i, 'sum'])
                    trade_data.at[index, "o_date"] = data.at[i, 'date']
                else:
                    trade_data.at[index, "i_total"] += int(data.at[i, 'sum'])

                trade_data.at[index, "amount"] += int(data.at[i, 'amount'])
                t_count += data.at[i, 'amount']

    return trade_data


def analysis_pre(trade_data):
    tmp = trade_data[trade_data["amount"] == 0]
    tmp['time'] = (tmp['o_date'] - tmp['i_date']).apply(lambda x: int(x.days))
    tmp['earning'] = tmp['o_total'] - tmp['i_total']
    tmp['pct'] = (tmp['earning'] / tmp['i_total']).apply(two_digit_percent)
    return tmp


def analysis1(trade_data):
    # 总的统计
    print("总收益：" + str(trade_data[trade_data['earning'] > 0].earning.sum()))
    print("总亏损：" + str(trade_data[trade_data['earning'] < 0].earning.sum()))
    print("合计：" + str(trade_data['earning'].sum()))

    print("成功次数：" + str(len(trade_data[trade_data['earning'] > 0])))
    print("失败次数：" + str(len(trade_data[trade_data['earning'] < 0])))
    print("成功率：" + str(two_digit_percent(len(trade_data[trade_data['earning'] > 0]) / len(trade_data))) + "%")

    print("涨幅大于5%的次数:" + str(len(trade_data[trade_data['pct'] > 5])))
    print("涨幅大于5%的收益:" + str(trade_data[trade_data['pct'] > 5].earning.sum()))

    print("跌幅大于5%的次数:" + str(len(trade_data[trade_data['pct'] < -5])))
    print("跌幅大于5% :" + str(trade_data[trade_data['pct'] < -5].earning.sum()))


def analysis2(trade_data):
    # 盈亏百分比对应数量和盈亏总和
    cuts = pd.cut(trade_data['pct'], [-20, -10, -5, 0, 5, 10, 20, 40, 80])
    groups = trade_data.groupby(cuts)
    # groups.apply(lambda x: x['earning'].sum())
    st_data = pd.DataFrame(
        {"count": groups.apply(lambda x: x['earning'].count()),
         "earning": groups.apply(lambda x: x['earning'].sum()),
         "time": groups.apply(lambda x: x['time'].mean())})

    # st_data.plot(x = "pct",y = "count",kind = "bar",figsize=(16,12))
    # st_data.plot(x = "pct",y = "earning",kind = "bar",figsize=(16,12))
    return st_data


def analysis3(trade_data):
    # 各个时间点买入卖出数量
    month_in_dis = trade_data['i_date'].map(lambda x: x.strftime('%m')).value_counts()
    month_out_dis = trade_data['o_date'].map(lambda x: x.strftime('%m')).value_counts()
    df = pd.DataFrame({'month_in': month_in_dis, 'month_out': month_out_dis})
    df.plot.bar()

    all_in_dis = trade_data['i_date'].map(lambda x: x.strftime('%Y-%m')).value_counts()
    all_out_dis = trade_data['o_date'].map(lambda x: x.strftime('%Y-%m')).value_counts()
    df = pd.DataFrame({'all_in': all_in_dis, 'all_out': all_out_dis})
    df.plot.bar()


# 每次django启动时调用，刷新交易数据
def store_trade():
    df = pd.read_excel(os.path.dirname(__file__) + "/data.xlsx")

    df = df.query('operation == \'证券买入\' or operation == \'证券卖出\'')

    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d", errors='raise')
    df['date'] = df['date'].apply(lambda x: x.date())
    df['date_str'] = df['date'].apply(lambda x: str(x))
    df['code'] = df['code'].apply(code_complete)
    # change 64types
    for i in df:
        type_str = str(df[i].dtype)
        if '64' in type_str:
            df[i] = df[i].astype(type_str[:-2])

    # remove useless columns
    for i in range(6):
        df.drop('useless' + str(i + 1), axis=1, inplace=True)

    t_data = get_trade(df)

    t_data1 = analysis_pre(t_data)

    if ('sqlite' in settings.DATABASES['default']['ENGINE']):
        url = 'sqlite:///' + settings.DATABASES['default']['NAME']
    else:
        url = 'mysql+pymysql://' + settings.DATABASES['default']['USER'] + ':' + settings.DATABASES['default'][
            'PASSWORD'] + '@localhost:3306/' + settings.DATABASES['default']['NAME'] + '?charset=utf8'
    yconnect = create_engine(url)

    t_data1['id'] = t_data1.index - 3
    t_data1.to_sql("statistic_trade_data", con=yconnect, if_exists='replace')

    df['id'] = df.index
    df.to_sql("original_trade_data", con=yconnect, if_exists='replace')
    '''
    for code in df['code'].drop_duplicates():
        dbtest.store_k_data(code, yconnect)
        break
    '''


if __name__ == '__main__':
    # use_proxy()
    df = pd.read_excel(os.path.dirname(__file__) + "/data.xlsx")

    df = df.query('operation == \'证券买入\' or operation == \'证券卖出\'')

    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d", errors='raise')
    df['date'] = df['date'].apply(lambda x: x.date())
    df['date_str'] = df['date'].apply(lambda x: str(x))
    df['code'] = df['code'].apply(code_complete)
    # change 64types
    for i in df:
        type_str = str(df[i].dtype)
        if '64' in type_str:
            df[i] = df[i].astype(type_str[:-2])

    # remove useless columns
    for i in range(6):
        df.drop('useless' + str(i + 1), axis=1, inplace=True)

    t_data = get_trade(df)

    t_data1 = analysis_pre(t_data)

    analysis1(t_data1)

    t_data2 = analysis2(t_data1)

    t_data3 = analysis3(t_data1)

    if ('sqlite' in settings.DATABASES['default']['ENGINE']):
        url = 'sqlite:///' + settings.DATABASES['default']['NAME']
    else:
        url = 'mysql+pymysql://' + settings.DATABASES['default']['USER'] + ':' + settings.DATABASES['default'][
            'PASSWORD'] + '@localhost:3306/' + settings.DATABASES['default']['NAME'] + '?charset=utf8'
    yconnect = create_engine(url)

    t_data1['id'] = t_data1.index - 3
    t_data1.to_sql("statistic_trade_data", con=yconnect, if_exists='replace')

    df['id'] = df.index
    df.to_sql("original_trade_data", con=yconnect, if_exists='replace')

    # 保存一只股票主要是创建一下表结构
    for code in df['code'].drop_duplicates():
        dbtest.store_k_data(code, yconnect)
        break
