# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import tushare as ts
import pandas

#前复权周线
df=ts.get_k_data('300144', ktype='W', autype='qfq')

#信息
#type(df)
#df.info()
#df.open.size
#len(df)
#length=len(df)

#数值判断
#if df.open[1:2]>2:
#    print('true')
#else:
#    print('small than 2')

#float(df.open[1:2])

#画图
#df.open.plot()

#过滤
#df[df.date>'2017-10-13']
#df[df.date='2016-10-31']
#df[df['date'].isin(['2010-12-17','2010-12-24'])]
#多层过滤
#df[df.date>'2017-10-13'][df.open<19.33]

#切片，多层切片
#df.iloc[5:21]
#df.iloc[5:21,1:4]
#df.iloc[5:21,[1,4]]
#df.loc[1:6,['date','close'] ]
#单个元素访问
#df.at[1,'close']

#多个条件
#df.query('operation == \'111\' or operation == \'222\'')

#取某几行
#tmp = data[['date','name','price','amount']]

dataOri={'date':[],'close':[],'pct_chg':[]}
for i in range(len(df)-1):
    dataOri['date'].append(df.date[i+1])
    dataOri['close'].append(df.close[i+1])
    pct=float(df.close[i+1]-df.close[i])/float(df.close[i])
    dataOri['pct_chg'].append(int(pct*10000)/100.0)
mydf=pandas.DataFrame(dataOri) 
    
    
