# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import tushare as ts
import pandas

#上涨，下跌开始判定涨跌比百分率，周线
UPpct = 3
DOWNpct = 3
#上涨，下跌微创新低则结束的判定周数
UPweeks = 3
DOWNweeks = 3

def kp2dig(number):
    #范围两位小数百分比
    pct=float(number)
    return (int(pct*10000)/100.0)

def get_bas_dat(data):
    #从初始数据中提取每周日期，收盘价，涨跌幅
    dataBas={'date':[],'close':[],'pct_chg':[]}
    pct_chg=data.close.pct_change()
    dataBas['date'].append(data.date[0])
    dataBas['close'].append(float(data.close[0]))
    dataBas['pct_chg'].append(pct_chg[0])
    
    for i in range(len(data)-1):
        dataBas['date'].append(data.date[i+1])
        dataBas['close'].append(float(data.close[i+1]))
        pct=float(pct_chg[i+1])
        dataBas['pct_chg'].append(kp2dig(pct))
    return pandas.DataFrame(dataBas) 

def get_ris_prd(data):
    #提取上升趋势的维持时间，涨幅
    #开始时间，上升幅度，持续周数
    risData={'start_date':[],'end_date':[],'ris_pct':[],'last_weeks':[]}
    
    #提取大于3%的涨幅，作为上涨趋势的初期的突破趋势,该幅度可调整
    ris_pct_index=data[data.pct_chg > UPpct].index
    endIndex = ris_pct_index[0]-1
    for i in ris_pct_index:
        
        #当前日期在上一个统计结果内,则自动进入下一个数据
        if i <= endIndex:
            #print(str(i)+':'+str(endIndex))
            continue
        
        endIndex=ris_judge(data,i)
        if endIndex != i:
            risData['start_date'].append(data.date[i])
            risData['end_date'].append(data.date[endIndex])
            begPrice = float(data.close[i-1])
            endPrice = float(data.close[endIndex])
            pct = kp2dig(endPrice/begPrice-1)
            risData['ris_pct'].append(pct)
            risData['last_weeks'].append(endIndex-i+1)
        else:
            if data.at[i,'pct_chg'] > 10:
                risData['start_date'].append(data.date[i])
                risData['end_date'].append(data.date[endIndex])
                risData['ris_pct'].append(float(data.pct_chg[i]))
                risData['last_weeks'].append(1)
    return pandas.DataFrame(risData)


  
def ris_judge(data,begIndex):
    
    #统计上涨趋势维持的时长
    curIndex = begIndex
    peakIndex = begIndex
    weekCount = 0
    
    #三周内未创新高择视为趋势结束，创新高则重新计时
    while(weekCount < UPweeks and curIndex < len(data)-1):
        curIndex += 1
        peak=float(data.close[peakIndex])
        cur=float(data.close[curIndex])
        if peak < cur:
            peakIndex = curIndex
            weekCount = 0
        else:
            weekCount += 1
    return peakIndex

def gen_ris_sta(data,risData):
    
    #对于上升趋势的总体统计
    result = ''
    result += '统计时间' + data.date[0] + '~' + data.date[len(data)-1] + ':\n' + '\n'
    result += str(risData1.loc[:,['start_date','end_date','ris_pct','last_weeks']]) + '\n\n'
        
    tempFloat = 0
    tempInt = 0
    
    #统计趋势中的超过上涨幅度UPpct（3）的k线
    for i in data[data.pct_chg > UPpct].index:
        if len(risData[risData.start_date < data.date[i]][risData.end_date > data.date[i]]) > 0:
            tempInt += 1
    tempFloat = kp2dig(len(risData)/(len(data[data.pct_chg > UPpct])-tempInt))
    result += '上涨百分比 >= ' + str(UPpct) + '% 的k线共 ' + str(len(data[data.pct_chg > UPpct])) + ' 个' + '\n'
    result += '其中形成趋势的有 ' + str(len(risData)) + ' 个k线' + '\n'
    result += '去除上涨趋势中的 ' + str(tempInt) + ' 条k线，形成趋势概率' + str(tempFloat) + '%' + '\n' + '\n'
    
    result += '平均上涨幅度: ' + str(kp2dig(risData.ris_pct.mean()/100)) + ' %' + '\n'
    result += '平均维持时长: ' + str(kp2dig(risData.last_weeks.mean()/100)) + ' 周' + '\n' + '\n'
    result += '形成的趋势中'
    result += '上涨幅度 >= 10% 的概率: ' + str(kp2dig(len(risData[risData.ris_pct >= 10 ])/len(risData))) + ' %' + '\n'
    result += '上涨时长 >= 3 周: ' + str(kp2dig(len(risData[risData.last_weeks >= 3 ])/len(risData))) + ' %' + '\n'

    print(result)
    return None

if __name__ == '__main__':
    data1=ts.get_k_data('002242', ktype='W', autype='qfq' ,index=False,start='2015-07-06', end='2017-11-09')
    stockData1=get_bas_dat(data1)
    risData1=get_ris_prd(stockData1)
    gen_ris_sta(stockData1,risData1)