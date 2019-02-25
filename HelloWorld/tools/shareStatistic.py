# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import tushare as ts
import pandas

#上涨，下跌开始判定涨跌比百分率，周线
upPct = 3
downPct = 3
#上涨，下跌微创新低则结束的判定周数
upTimes = 3
downTimes = 3

def kp2dig(number):
    #范围两位小数百分比
    pct=float(number)
    return (int(pct*10000)/100.0)

class Share:
    
    code='000001'
    kType='W'
    oriData=None
    risData=None
    
    startDate='2005-07-06'
    endDate='2019-11-09'
    #上涨，下跌开始判定涨跌比百分率，周线
    upPct = 3
    downPct = 3
    #上涨，下跌微创新低则结束的判定周数
    upTimes = 3
    downTimes = 3
    
    oriData = None
    basData = None
    rstDic={}
    
    def get_bas_dat(self,data):
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
    
    def ris_judge(self,data,begIndex):
        
        #统计上涨趋势维持的时长
        curIndex = begIndex
        peakIndex = begIndex
        weekCount = 0
        
        #三周内未创新高择视为趋势结束，创新高则重新计时
        while(weekCount < upTimes and curIndex < len(data)-1):
            curIndex += 1
            peak=float(data.close[peakIndex])
            cur=float(data.close[curIndex])
            if peak < cur:
                peakIndex = curIndex
                weekCount = 0
            else:
                weekCount += 1
        return peakIndex
    
    def get_ris_prd(self,data):
        #提取上升趋势的维持时间，涨幅
        #开始时间，上升幅度，持续周数
        risData={'start_date':[],'end_date':[],'ris_pct':[],'last_weeks':[]}
        
        #提取大于3%的涨幅，作为上涨趋势的初期的突破趋势,该幅度可调整
        ris_pct_index=data[data.pct_chg > upPct].index
        endIndex = ris_pct_index[0]-1
        for i in ris_pct_index:
            
            #当前日期在上一个统计结果内,则自动进入下一个数据
            if i <= endIndex:
                #print(str(i)+':'+str(endIndex))
                continue
            
            endIndex = self.ris_judge(data,i)
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
    
    def gen_ris_sta(self,data,risData):
        
        if self.kType=='D':
            timeUnit='天'
        elif self.kType=='W':
            timeUnit='周'
        else:
            timeUnit='月'
                
        #对于上升趋势的总体统计
        self.rstDic={}
        result = ''
        result += '统计时间' + data.date[0] + '~' + data.date[len(data)-1] + ':\n' + '\n'
        result += str(risData.loc[:,['start_date','end_date','ris_pct','last_weeks']]) + '\n\n'
            
        tempFloat = 0
        tempInt = 0
        
        #统计趋势中的超过上涨幅度upPct（3）的k线
        for i in data[data.pct_chg > upPct].index:
            if len(risData[risData.start_date < data.date[i]][risData.end_date > data.date[i]]) > 0:
                tempInt += 1
        tempFloat = kp2dig(len(risData)/(len(data[data.pct_chg > upPct])-tempInt))
        
        self.rstDic["total_numbers"] = len(data[data.pct_chg > upPct])
        result += '上涨百分比 >= ' + str(upPct) + '% 的k线共 ' + str(self.rstDic["total_numbers"]) + ' 个' + '\n'
        self.rstDic["succeed_numbers"] = len(risData)
        result += '其中形成趋势的有 ' + str(self.rstDic["succeed_numbers"]) + ' 个k线' + '\n'
        self.rstDic["in_succeed_numbers"] = tempInt
        self.rstDic["win_rate"] = tempFloat
        result += '去除上涨趋势中的 ' + str(tempInt) + ' 条k线，形成趋势概率' + str(tempFloat) + '%' + '\n' + '\n'
        result += '平均上涨幅度: ' + str(kp2dig(risData.ris_pct.mean()/100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(risData.last_weeks.mean()/100)) + timeUnit + '\n' + '\n'
        result += '形成的趋势中'
        result += '上涨幅度 >= 10% 的概率: ' + str(kp2dig(len(risData[risData.ris_pct >= 10 ])/len(risData))) + ' %' + '\n'
        result += '上涨时长 >= ' + str(upTimes) + timeUnit + ': ' + str(kp2dig(len(risData[risData.last_weeks >= 3 ])/len(risData))) + ' %' + '\n'
    
        print(result)
        return None
    
    def statistic(self):
        self.oriData = ts.get_k_data(self.code, ktype=self.kType, autype='qfq', index=False, start=self.startDate, end=self.endDate)          
        self.oriData.index = self.oriData.index - self.oriData.index[0]
        self.basData = self.get_bas_dat(self.oriData)
        self.risData = self.get_ris_prd(self.basData)
        self.rstDic = self.gen_ris_sta(self.basData,self.risData)        

if __name__ == '__main__':
    share = Share()
    share.statistic()