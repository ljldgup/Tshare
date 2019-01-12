# -*- coding: utf-8 -*-
"""
Created on Sun Aug  5 00:18:51 2018

@author: ljl
"""
import dbtest
import pandas as pd
from sqlalchemy import create_engine
import os,sys
sys.path.append("..")
from HelloWorld import settings

def use_proxy():
    HTTP_PROXY = "http_proxy"
    HTTPS_PROXY = "https_proxy"
    os.environ[HTTP_PROXY] = "cn-proxy.jp.oracle.com:80"
    os.environ[HTTPS_PROXY] = "cn-proxy.jp.oracle.com:80"
    print (os.environ["http_proxy"])
    print (os.environ["https_proxy"])

def kp2dig(number):
    #范围两位小数百分比
    return float('%.5f' % (number))

#补全股票代码
def code_complete(code):
    s_code = str(code)
    for i in range(6-len(s_code)):
        s_code = '0' + s_code
    return s_code


#每个股票的每次交易数据统计
def get_trade(data):

    index = -1

    trade_data = pd.DataFrame(columns = ["code","name", "i_date", "o_date", "i_total","o_total","amount"])

    for name in data.name.drop_duplicates():
        t_count = 0
        getsum = 0
        getamount = 0
        for i in data[data.name == name].index:
            if data.at[i,'amount'] < 0:
                getsum -= int(data.at[i,'sum'])
            else:
                getsum += int(data.at[i,'sum'])
            getamount += int(data.at[i,'amount'])
            data.at[i,'getamount'] = getamount

            #手数为0后持仓就是亏损
            if getamount == 0:
                data.at[i,'getsum'] = -getsum
                getsum = 0

            #新的交易
            if t_count == 0:
                index += 1
                trade_data.at[index,"name"] = name
                trade_data.at[index,"code"] = data.at[i,'code']
                trade_data.at[index,"i_date"] = data.at[i,'date']
                trade_data.at[index,"i_total"] = int(data.at[i,'sum'])
                trade_data.at[index,"o_total"] = 0
                trade_data.at[index,"amount"] = int(data.at[i,'amount'])
                t_count = data.at[i,'amount']

            else:
                trade_data.at[index,"name"] = name

                if data.at[i,'amount'] < 0:
                    trade_data.at[index,"o_total"] += int(data.at[i,'sum'])
                    trade_data.at[index,"o_date"] = data.at[i,'date']
                else:
                    trade_data.at[index,"i_total"] += int(data.at[i,'sum'])

                trade_data.at[index,"amount"] += int(data.at[i,'amount'])
                t_count += data.at[i,'amount']

    return trade_data

def analysis_pre(trade_data):
    tmp = trade_data[trade_data.amount == 0]
    tmp['time'] = tmp['o_date'] - tmp['i_date']
    tmp['time'] = tmp['time'].apply(lambda x : x.days)
    tmp['time'] = tmp['time'].astype(int)
    tmp['earning'] = tmp['o_total'] - tmp['i_total']
    tmp['pct'] = tmp['earning']/tmp['i_total']*100
    tmp['pct'] = tmp['pct'].apply(kp2dig)
    return tmp

def analysis1(trade_data):
    #总的统计
    print("总收益：" + str(trade_data[trade_data.earning > 0].earning.sum()))
    print("总亏损：" + str(trade_data[trade_data.earning < 0].earning.sum()))
    print("合计：" + str(trade_data.earning.sum()))

    print("成功次数：" + str(len(trade_data[trade_data.earning > 0])))
    print("失败次数：" + str(len(trade_data[trade_data.earning < 0])))
    print("成功率：" + str(kp2dig(len(trade_data[trade_data.earning > 0])/len(trade_data))*100) + "%")

    print("涨幅大于5%的次数:" + str(len(trade_data[trade_data.pct > 5])))
    print("涨幅大于5%的收益:" + str(trade_data[trade_data.pct > 5].earning.sum()))

    print("跌幅大于5%的次数:" + str(len(trade_data[trade_data.pct < -5])))
    print("跌幅大于5%的收益:" + str(trade_data[trade_data.pct < -5].earning.sum()))


def analysis2(trade_data):
    #盈亏百分比对应数量和盈亏总和
    tmax=int(trade_data.pct.max()+1)
    tmin=int(trade_data.pct.min()-1)
    st_data = pd.DataFrame(columns = ["pct", "count", "earning","time"])

    index = 0
    for i in range(tmin,tmax):
        st_data.at[index,"pct"] = str(i) + "-" + str(i+1)
        tmp = trade_data[trade_data.pct > i]
        tmp = tmp[tmp.pct < i+1]
        st_data.at[index,"count"] = len(tmp)
        st_data.at[index,"earning"] = tmp.earning.sum()
        if len(tmp) != 0:
            st_data.at[index,"time"] = tmp.time.sum()/len(tmp)
        st_data.at[index,"count"] = len(tmp)
        index += 1

    index = 0

    #st_data.plot(x = "pct",y = "count",kind = "bar",figsize=(16,12))
    #st_data.plot(x = "pct",y = "earning",kind = "bar",figsize=(16,12))
    return st_data



def analysis3(trade_data):
    #各个时间点买入卖出数量
    tmax=trade_data.i_date.max()
    tmin=trade_data.i_date.min()

    st_data1 = pd.DataFrame(columns = ["date", "count", "earning","win_rate"])

    index = 0
    tmp = tmin.replace(tmin.year,tmin.month,1)
    while tmp < tmax:
        if tmp.month != 12:
            ntmp= tmp.replace(tmp.year,tmp.month + 1,1)
        else:
            ntmp= tmp.replace(tmp.year+1,1,1)
        st_data1.at[index,'date'] = tmp
        t = trade_data[trade_data.i_date > tmp]
        t = t[t.i_date < ntmp]
        st_data1.at[index,'count'] = t.i_date.count()
        st_data1.at[index,'earning'] = t.earning.sum()
        st_data1.at[index,'win_rate'] = t[t.earning>0].count()/t.count()
        tmp = ntmp
        index += 1

    #st_data1.plot(x = "date",y = "count",kind = "bar",figsize=(16,12))
    return st_data1

    tmax=trade_data.o_date.max()
    tmin=trade_data.o_date.min()

    st_data2 = pd.DataFrame(columns = ["date", "count", "earning", "win_rate"])

    index = 0
    tmp = tmin.replace(tmin.year,tmin.month,1)
    while tmp < tmax:
        if tmp.month != 12:
            ntmp= tmp.replace(tmp.year,tmp.month + 1,1)
        else:
            ntmp= tmp.replace(tmp.year+1,1,1)
        st_data2.at[index,'date'] = tmp
        t = trade_data[trade_data.o_date > tmp]
        t = t[t.o_date < ntmp]
        st_data2.at[index,'count'] = t.o_date.count()
        st_data2.at[index,'earning'] = t.earning.sum()
        st_data2.at[index,'win_rate'] = t[t.earning > 0].count()/t.count()
        tmp = ntmp
        index += 1
    #st_data2.plot(x = "date",y = "count", kind = "bar",figsize=(16,12))
    return st_data2

if __name__ == '__main__':
    #use_proxy()
    df = pd.read_excel("data.xlsx")

    df = df.query('operation == \'证券买入\' or operation == \'证券卖出\'')

    df['date'] = pd.to_datetime(df['date'],format="%Y-%m-%d",errors='raise')
    df['date'] = df.date.apply(lambda x:x.date())
    df['date_str'] = df.date.apply(lambda x:str(x))
    df['code'] = df.code.apply(code_complete)
    #change 64types
    for i in df:
        type_str = str(df[i].dtype)
        if '64' in type_str:
            df[i] = df[i].astype(type_str[:-2])

    #remove useless columns
    for i in range(6):
        df.drop('useless' + str(i+1), axis=1, inplace=True)

    t_data = get_trade(df)

    t_data1 = analysis_pre(t_data)

    analysis1(t_data1)

    t_data2 = analysis2(t_data1)

    t_data3 = analysis3(t_data1)

    if('sqlite' in settings.DATABASES['default']['ENGINE']):
        url= 'sqlite:///' + settings.DATABASES['default']['NAME']
    else:
        url = 'mysql+pymysql://' + settings.DATABASES['default']['USER'] + ':' + settings.DATABASES['default']['PASSWORD'] + '@localhost:3306/' + settings.DATABASES['default']['NAME'] + '?charset=utf8'
    yconnect = create_engine(url)

    t_data1['id']= t_data1.index -3
    t_data1.to_sql("statistic_trade_data",con=yconnect,if_exists='replace')

    df['id']=  df.index
    df.to_sql("original_trade_data",con=yconnect,if_exists='replace')

    for code in df.code.drop_duplicates():
        dbtest.storekdata(code,yconnect)
        break

