# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import tushare as ts
import pandas

def kp2dig(number):
    #范围两位小数百分比
    pct=float(number)
    return (int(pct*10000)/100.0)

class Share:
    
    #上行趋势起始判断涨幅，多少个周期数内未创新稿就结束，涨幅
    upStartPct=2
    upLastTimes=4
    upPct=10
    
    downStartPct=2
    downLastTimes=4
    downPct=10
    
    def __init__(self, code, kType, startDate, endDate):
        self.code = code
        self.kType = kType
        self.startDate = startDate
        self.endDate = endDate
        
    def setJudgeCondition(self, upStartPct, upLastTimes, upPct, downStartPct, downLastTimes, downPct):
        #上涨，下跌开始判定涨跌比百分率
        #上涨，下跌微创新低则结束的判定周期次数
        self.upStartPct = upStartPct
        self.upLastTimes = upLastTimes
        self.upPct = upPct
        self.downStartPct = downStartPct
        self.downLastTimes = downLastTimes
        self.downPct = downPct
        
    def get_bas_dat(self , data):
        
        #从初始数据中提取每周日期，收盘价，涨跌幅
        dataBas = {'date':[], 'open':[],'close':[],'pct_chg':[]}
        pct_chg = data.close.pct_change()
        dataBas['date'].append(data.date[0])
        dataBas['close'].append(float(data.close[0]))
        dataBas['open'].append(float(data.open[0]))
        dataBas['pct_chg'].append(pct_chg[0])
        
        for i in range(len(data)-1):
            dataBas['date'].append(data.date[i+1])
            dataBas['close'].append(float(data.close[i+1]))
            dataBas['open'].append(float(data.open[i+1]))
            pct = float(pct_chg[i+1])
            dataBas['pct_chg'].append(kp2dig(pct))
        return pandas.DataFrame(dataBas) 
    
    #统计上涨或下跌的趋势维持的时长
    #返回结束的Index
    def trend_judge(self, data, begIndex):
        
       
        beginPct = data.pct_chg[begIndex]
        
        curIndex = begIndex
        peakIndex = begIndex
        
        #确定涨跌
        if beginPct > 0 :
            upLastTimes = self.upLastTimes
            judge = lambda x,y: x>y
            
        else:
            upLastTimes = self.downLastTimes
            judge = lambda x,y: x<y
            
        weekCount = 0
        #三周内未创新高择视为趋势结束，创新高则重新计计数
        while(weekCount < upLastTimes and curIndex < len(data)-1):
            curIndex += 1
            peak = float(data.close[peakIndex])
            cur = float(data.close[curIndex])
            
            if judge(peak, cur):
                peakIndex = curIndex
                weekCount = 0
                
            else:
                #未创新高累计周数
                weekCount += 1
                
        return peakIndex
    
    
    def get_trend_prd(self,data):
        #提取上升下降趋势的维持时间，涨幅
        #开始时间，上升幅度，持续周数
        trendData={'start_date':[], 'end_date':[], 'pct':[], 'last_weeks':[], 'open':[], 'close':[]}
        
        #提取大于3%的涨幅，作为上涨趋势的初期的突破趋势,该幅度可调整
        ris_pct_index = data.query('pct_chg > ' + str(self.upStartPct) + ' or pct_chg < ' + str(self.downStartPct) )
        endIndex = ris_pct_index.index[0]-1
        i = ris_pct_index.index[0] - 1
        
        for i in ris_pct_index.index:
            
            if i < endIndex:
                continue
            
            endIndex = self.trend_judge(data, i)
            
            if endIndex != i:
                begPrice = float(data.close[i])
                endPrice = float(data.close[endIndex])
                pct = kp2dig(endPrice/begPrice-1)
                
                if pct > self.upPct or pct < self.downPct:
                    trendData['start_date'].append(data.date[i+1])
                    trendData['end_date'].append(data.date[endIndex])
                    trendData['pct'].append(pct)
                    trendData['last_weeks'].append(endIndex-i+1)
                    trendData['open'].append(data.close[i])
                    trendData['close'].append(data.close[endIndex])
                
            #如果涨幅大于upPct 
            elif data.at[i,'pct_chg'] > self.upPct or data.at[i,'pct_chg'] < self.downPct :
                trendData['start_date'].append(data.date[i])
                trendData['end_date'].append(data.date[endIndex+1])
                trendData['pct'].append(float(data.pct_chg[i]))
                trendData['last_weeks'].append(1)
                trendData['open'].append(data.open[i])
                trendData['close'].append(data.close[i])
                    
        return pandas.DataFrame(trendData)
    
    def gen_ris_sta(self, pct, time):
        
        #涨幅大于pct大概率 和时长大于time的概率
        
        data = self.basData
        trendData = self.trendData
        
        #对于上升趋势的总体统计
        if self.kType=='D':
            timeUnit='天'
        elif self.kType=='W':
            timeUnit='周'
        else:
            timeUnit='月'
                
   
        result = ''
        result += '统计时间' + data.date[0] + '~' + data.date[len(data)-1] + ':\n' + '\n'
            
        tempFloat = 0
        tempInt = 0
        
        #综合统计
        #统计趋势中的超过上涨幅度upStartPct的k线
        for i in data[data.pct_chg > self.upStartPct].index:
            if len(trendData[trendData.start_date < data.date[i]][trendData.end_date > data.date[i]]) > 0:
                tempInt += 1
        tempFloat = kp2dig(len(trendData)/(len(data[data.pct_chg > self.upStartPct])-tempInt))
        
        result += '上涨百分比 >= ' + str(self.upStartPct) + '% 的k线共 ' + str(len(data[data.pct_chg > self.upStartPct])) + ' 个' + '\n'
        result += '其中形成趋势的有 ' + str(len(trendData)) + ' 个k线' + '\n'
        result += '去除上涨趋势中的 ' + str(tempInt) + ' 条k线，形成趋势概率' + str(tempFloat) + '%' + '\n' + '\n'
        result += '平均上涨幅度: ' + str(kp2dig(trendData.pct.mean()/100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(trendData.last_weeks.mean()/100)) + timeUnit + '\n' + '\n'
        
        print(result)
        
        #具体统计
        result = '形成的趋势中'
        result += '上涨幅度 >= ' + str(pct) + '% 的概率: ' + str(kp2dig(len(trendData[trendData.pct >= pct ])/len(trendData))) + ' %' + '\n'
        result += '上涨时长 >= ' + str(time) + timeUnit + ': ' + str(kp2dig(len(trendData[trendData.last_weeks >= time ])/len(trendData))) + ' %' + '\n'
        print(result)
        return trendData[trendData.pct >= pct ]
        
        

    def gen_down_sta(self, pct, time):
        
        #跌幅大于pct大概率 和时长大于time的概率
        data = self.basData
        trendData = self.trendData
        
        #对于上升趋势的总体统计
        if self.kType=='D':
            timeUnit='天'
        elif self.kType=='W':
            timeUnit='周'
        else:
            timeUnit='月'
                
   
        result = ''
        result += '统计时间' + data.date[0] + '~' + data.date[len(data)-1] + ':\n' + '\n'
            
        tempFloat = 0
        tempInt = 0
        
        #趋势综合统计
        #统计趋势中的超过上涨幅度upStartPct的k线（下行相反）
        for i in data[data.pct_chg < self.downStartPct].index:
            if len(trendData[trendData.start_date < data.date[i]][trendData.end_date > data.date[i]]) > 0:
                tempInt += 1
        tempFloat = kp2dig(len(trendData)/(len(data[data.pct_chg > self.downStartPct])-tempInt))
        
        result += '下跌百分比 <= ' + str(self.downStartPct) + '% 的k线共 ' + str(len(data[data.pct_chg > self.upStartPct])) + ' 个' + '\n'
        result += '其中形成下跌趋势的有 ' + str(len(trendData)) + ' 个k线' + '\n'
        result += '去除下跌趋势中的 ' + str(tempInt) + ' 条k线，形成趋势概率' + str(tempFloat) + '%' + '\n' + '\n'
        result += '平均下跌幅度: ' + str(kp2dig(trendData.pct.mean()/100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(trendData.last_weeks.mean()/100)) + timeUnit + '\n' + '\n'
        print(result)
        
        result = '形成的趋势中'
        result += '下跌幅度 <= ' + str(pct) + '% 的概率: ' + str(kp2dig(len(trendData[trendData.pct < pct ])/len(trendData))) + ' %' + '\n'
        result += '下跌时长 >= ' + str(time) + timeUnit + ': ' + str(kp2dig(len(trendData[trendData.last_weeks >= time ])/len(trendData))) + ' %' + '\n'
        print(result)
        return trendData[trendData.pct <= pct ]
        
    
    def statistic(self):
        self.oriData = ts.get_k_data(self.code, ktype=self.kType, autype='qfq', index=False, start=self.startDate, end=self.endDate)          
        self.oriData.index = self.oriData.index - self.oriData.index[0]
        self.basData = self.get_bas_dat(self.oriData)
        self.trendData = self.get_trend_prd(self.basData)
        #self.gen_ris_sta()        

if __name__ == '__main__':
    #上证指数
    szIndex = Share('sh', 'W', '2000-07-06' , '2019-07-06')
    szIndex.setJudgeCondition(1, 3, 10, -1.5, 3, -10)
    szIndex.statistic()
    #szIndex.gen_ris_sta(34, 10)
    szIndex.gen_down_sta(-5, 4)