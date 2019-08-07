# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import tushare as ts
import pandas,os

def use_proxy():
    HTTP_PROXY = "http_proxy"
    HTTPS_PROXY = "https_proxy"
    os.environ[HTTP_PROXY] = "cn-proxy.jp.oracle.com:80"
    os.environ[HTTPS_PROXY] = "cn-proxy.jp.oracle.com:80"
    print (os.environ["http_proxy"])
    print (os.environ["https_proxy"])

def kp2dig(number):
    # 范围两位小数百分比
    pct = float(number)
    return (int(pct * 10000) / 100.0)


class Share:
    # 上行趋势起始判断涨幅，多少个周期数内未创新稿就结束，涨幅
    upStartPct = 2
    upLastTimes = 4
    upPct = 10

    downStartPct = 2
    downLastTimes = 4
    downPct = 10

    def __init__(self, code, kType, startDate, endDate):
        self.code = code
        self.kType = kType
        self.startDate = startDate
        self.endDate = endDate
        if self.kType == 'D':
            self.timeUnit = '天'
        elif self.kType == 'W':
            self.timeUnit = '周'
        else:
            self.timeUnit = '月'

        #默认上涨下跌判断条件
        self.upStartPct = 1
        self.upLastTimes = 1
        self.upPct = 15
        self.downStartPct = 1
        self.downLastTimes = 1
        self.downPct = 15

    def setJudgeCondition(self, upStartPct, upLastTimes, upPct, downStartPct, downLastTimes, downPct):
        # 上涨，下跌开始判定涨跌比百分率，持续时间，合格百分比
        # 上涨，下跌微创新低则结束的判定周期次数
        self.upStartPct = upStartPct
        self.upLastTimes = upLastTimes
        self.upPct = upPct
        self.downStartPct = downStartPct
        self.downLastTimes = downLastTimes
        self.downPct = downPct

    #获取原始数据self.oriData, 经过加工的基本数据self.basData
    def getBasDat(self):
        #获取原始数据
        self.oriData = ts.get_k_data(self.code, ktype = self.kType, autype = 'qfq', index = False,
                                     start = self.startDate, end = self.endDate)
        self.oriData.index = self.oriData.index - self.oriData.index[0]

        data = self.oriData
        # 从初始数据中提取每周日期，收盘价，涨跌幅
        dataBas = {'date': [], 'open': [], 'close': [], 'pctChg': [], 'volume': []}
        pctChg = data.close.pct_change()
        dataBas['date'].append(data.date[0])
        dataBas['close'].append(float(data.close[0]))
        dataBas['open'].append(float(data.open[0]))
        dataBas['pctChg'].append(pctChg[0])
        dataBas['volume'].append(data.volume[0])

        for i in range(len(data) - 1):
            dataBas['date'].append(data.date[i + 1])
            dataBas['close'].append(float(data.close[i + 1]))
            dataBas['open'].append(float(data.open[i + 1]))
            pct = float(pctChg[i + 1])
            dataBas['pctChg'].append(kp2dig(pct))
            dataBas['volume'].append(data.volume[i + 1])

        t = pandas.DataFrame(dataBas)
        self.basData = t.fillna(0)
        return self.basData

    # 统计上涨或下跌的趋势维持的时长
    # 返回结束的Index，如果不合格则返回值与输入相同
    def trendJudge(self, data, begIndex):

        beginPct = data.pctChg[begIndex]

        curIndex = begIndex
        peakIndex = begIndex

        # 确定涨跌
        if beginPct > 0:
            upLastTimes = self.upLastTimes
            judge = lambda x, y: x > y

        else:
            upLastTimes = self.downLastTimes
            judge = lambda x, y: x < y
            self.formerDown = begIndex

        weekCount = 0
        # 三周内未创新高择视为趋势结束，创新高则重新计计数
        while (weekCount < upLastTimes and curIndex < len(data) - 1):
            curIndex += 1
            peak = float(data.close[peakIndex])
            cur = float(data.close[curIndex])

            if judge(cur, peak):
                peakIndex = curIndex
                weekCount = 0

            else:
                # 未创新高累计周数
                weekCount += 1

        return peakIndex

    #从基本数据self.basData提取趋势数据 self.trendData
    def getTrendPrd(self):

        data = self.basData

        # 提取上升下降趋势的维持时间，涨幅
        # 开始时间，上升幅度，持续周数
        trendData = {'startDate': [], 'endDate': [], 'pct': [], 'lastWeeks': [], 'open': [], 'close': [], 'beginIndex': [], 'endIndex': []}

        # 提取大于3%的涨幅，作为上涨趋势的初期的突破趋势,该幅度可调整
        ris_pct_index = data.query('pctChg > ' + str(self.upStartPct) + ' or pctChg < ' + str(self.downStartPct))
        endIndex = ris_pct_index.index[0] - 1
        i = ris_pct_index.index[0] - 1

        for i in ris_pct_index.index:

            if i <= endIndex:
                continue

            tmpIndex = self.trendJudge(data, i)

            if endIndex != i:
                # print('{0},{1},{2},{3}'.format(i,tmpIndex,data.date[i],data.date[tmpIndex]))
                # 注意是前一周的收盘价，不是当前周的开盘价，涨跌幅都是收盘价算的
                begPrice = float(data.close[i - 1])
                endPrice = float(data.close[tmpIndex])
                pct = kp2dig(endPrice / begPrice - 1)
                # print('{0},{1},{2}'.format(begPrice,endPrice,pct))

                if pct > self.upPct or pct < self.downPct:
                    endIndex = tmpIndex
                    trendData['startDate'].append(data.date[i])
                    trendData['endDate'].append(data.date[endIndex])
                    trendData['pct'].append(pct)
                    trendData['lastWeeks'].append(endIndex - i + 1)
                    trendData['open'].append(data.close[i - 1])
                    trendData['close'].append(data.close[endIndex])
                    trendData['beginIndex'].append(i)
                    trendData['endIndex'].append(endIndex)

        # 调整一下列名顺序，DateFrame创建时列名按字母排序
        order = ['startDate', 'endDate', 'pct', 'lastWeeks', 'open', 'close', 'beginIndex', 'endIndex']
        self.trendData = pandas.DataFrame(trendData)[order]

    def getSecondaryTrendData(self):

        trendData = self.trendData
        #取得回调,反弹
        #次级折返趋势
        #spacePct折返幅度占之前的比例
        #timePct折返持续时间占之前的比例
        secondaryTrendData = {'startDate': [], 'endDate': [], 'lastWeeks': [], 'pct': [], 'spacePct': [], 'timePct': []}

        #合并趋势
        mergedTrendData = {'startDate': [], 'endDate': [], 'pct': [], 'lastWeeks': [], 'open': [], 'close': []}

        risTrendData = trendData[trendData.pct > 0]
        downTrendData = trendData[trendData.pct < 0]

        #回调统计
        flag = 0
        for index in risTrendData.index:
            if flag == 0 :
                #开始，上一个
                former = index
                last = index
                flag = 1

            elif (risTrendData.close[index] > risTrendData.close[last]
                and risTrendData.open[index] >= risTrendData.open[last]):
                secondaryTrendData['startDate'].append(risTrendData.endDate[last])
                secondaryTrendData['endDate'].append(risTrendData.startDate[index])
                secondaryTrendData['lastWeeks'].append(risTrendData.beginIndex[index] - risTrendData.endIndex[last])
                secondaryTrendData['pct'].append(kp2dig((risTrendData.close[last] - risTrendData.close[index]) / risTrendData.close[last]))
                secondaryTrendData['spacePct'].append(kp2dig((risTrendData.close[last] - risTrendData.open[index]) / (risTrendData.close[last] - risTrendData.open[last])))
                secondaryTrendData['timePct'].append(kp2dig((risTrendData.beginIndex[index] - risTrendData.endIndex[last]) / risTrendData.lastWeeks[last]))
                last = index

            else:
                mergedTrendData['startDate'].append(risTrendData.startDate[former])
                mergedTrendData['endDate'].append(risTrendData.endDate[last])
                mergedTrendData['lastWeeks'].append(risTrendData.endIndex[last] - risTrendData.beginIndex[former])
                mergedTrendData['pct'].append(kp2dig((risTrendData.close[last] - risTrendData.open[former])/risTrendData.open[former]))
                mergedTrendData['open'].append(risTrendData.open[former])
                mergedTrendData['close'].append(risTrendData.close[last])
                former = index
                last = index

        #反弹统计
        flag = 0
        for index in downTrendData.index:
            if flag == 0 :
                former = index
                last = index
                flag = 1

            elif (downTrendData.close[index] < downTrendData.close[last]
                and downTrendData.open[index] <= downTrendData.open[last]):
                secondaryTrendData['startDate'].append(downTrendData.endDate[last])
                secondaryTrendData['endDate'].append(downTrendData.startDate[index])
                secondaryTrendData['lastWeeks'].append(downTrendData.beginIndex[index] - downTrendData.endIndex[last])
                secondaryTrendData['pct'].append(kp2dig((downTrendData.close[last] - downTrendData.close[index]) / downTrendData.close[last]))
                secondaryTrendData['spacePct'].append(kp2dig((downTrendData.close[last] - downTrendData.open[index]) / (downTrendData.close[last] - downTrendData.open[last])))
                secondaryTrendData['timePct'].append(kp2dig((downTrendData.beginIndex[index] - downTrendData.endIndex[last]) / downTrendData.lastWeeks[last]))
                last = index

            else:
                mergedTrendData['startDate'].append(downTrendData.startDate[former])
                mergedTrendData['endDate'].append(downTrendData.endDate[last])
                mergedTrendData['lastWeeks'].append(downTrendData.endIndex[last] - downTrendData.beginIndex[former])
                mergedTrendData['pct'].append(kp2dig((downTrendData.close[last] - downTrendData.open[former])/downTrendData.open[former]))
                mergedTrendData['open'].append(downTrendData.open[former])
                mergedTrendData['close'].append(downTrendData.close[last])
                former = index
                last = index

        self.secondaryTrendData = pandas.DataFrame(secondaryTrendData)[['startDate', 'endDate', 'lastWeeks', 'pct', 'spacePct', 'timePct']]
        self.mergedTrendData = pandas.DataFrame(mergedTrendData)[['startDate', 'endDate', 'pct', 'lastWeeks', 'open', 'close']]

    def genRisSta(self):
        # 对于上升趋势的总体统计
        data = self.basData
        trendData = self.trendData[self.trendData.pct > 0]

        result = ''
        result += '统计时间' + data.date[0] + '~' + data.date[len(data) - 1] + ':\n' + '\n'

        tempFloat = 0
        tempInt = 0

        # 综合统计
        # 统计趋势中的超过上涨幅度upStartPct的k线
        for i in data[data.pctChg > self.upStartPct].index:
            if len(trendData[trendData.startDate < data.date[i]][trendData.endDate > data.date[i]]) > 0:
                tempInt += 1
        tempFloat = kp2dig(len(trendData) / (len(data[data.pctChg > self.upStartPct]) - tempInt))

        result += '上涨百分比 >= ' + str(self.upStartPct) + '% 的k线共 ' + str(
            len(data[data.pctChg > self.upStartPct])) + ' 个' + '\n'
        result += '其中形成趋势的有 ' + str(len(trendData)) + ' 个k线' + '\n'
        result += '去除上涨趋势中的 ' + str(tempInt) + ' 条k线，形成趋势概率' + str(tempFloat) + '%' + '\n' + '\n'
        result += '平均上涨幅度: ' + str(kp2dig(trendData.pct.mean() / 100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(trendData.lastWeeks.mean() / 100)) + self.timeUnit + '\n' + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

    def genRisTrend(self, pct, time):
        # 涨幅大于pct大概率 和时长大于time的概率
        trendData = self.trendData[self.trendData.pct > 0]

        result = '形成的趋势中'

        # 根据统计，上涨幅度增加的可能性
        result += '上涨幅度 >= ' + str(pct) + '% 的概率: ' + str(
            kp2dig(len(trendData[trendData.pct >= pct]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.pct >= pct ]) + '\n'

        # 根据统计，上涨时长增加的可能性
        result += '上涨时长 >= ' + str(time) + self.timeUnit + ': ' + str(
            kp2dig(len(trendData[trendData.lastWeeks >= time]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.lastWeeks >= time ]) + '\n'

        # 上涨猛烈程度评判
        result += str(time) + self.timeUnit + '内上涨幅度 >= ' + str(pct) + '%的概率: ' + str(
            kp2dig(len(trendData[trendData.lastWeeks < time][trendData.pct >= pct]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.lastWeeks < time][trendData.pct > pct]) + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

    def genDownSta(self):

        data = self.basData
        trendData = self.trendData[self.trendData.pct < 0]

        # 对于上升趋势的总体统计

        result = ''
        result += '统计时间' + data.date[0] + '~' + data.date[len(data) - 1] + ':\n' + '\n'

        tempFloat = 0
        tempInt = 0

        # 趋势综合统计
        # 统计趋势中的超过上涨幅度upStartPct的k线（下行相反）
        for i in data[data.pctChg < self.downStartPct].index:
            if len(trendData[trendData.startDate < data.date[i]][trendData.endDate > data.date[i]]) > 0:
                tempInt += 1
        tempFloat = kp2dig(len(trendData) / (len(data[data.pctChg < self.downStartPct]) - tempInt))

        result += '下跌百分比 <= ' + str(self.downStartPct) + '% 的k线共 ' + str(
            len(data[data.pctChg < self.downStartPct])) + ' 个' + '\n'
        result += '其中形成下跌趋势的有 ' + str(len(trendData)) + ' 个k线' + '\n'
        result += '去除下跌趋势中的 ' + str(tempInt) + ' 条k线，形成趋势概率' + str(tempFloat) + '%' + '\n' + '\n'
        result += '平均下跌幅度: ' + str(kp2dig(trendData.pct.mean() / 100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(trendData.lastWeeks.mean() / 100)) + self.timeUnit + '\n' + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

    def genDownTrend(self, pct, time):
        # 跌幅大于pct大概率 和时长大于time的概率
        trendData = self.trendData[self.trendData.pct < 0]
        result = '形成的趋势中'

        # 根据统计，下跌幅度扩大的可能性
        result += '幅度:下跌幅度 <= ' + str(pct) + '% 的概率: ' + str(
            kp2dig(len(trendData[trendData.pct <= pct]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.pct < pct]) + '\n'

        # 根据统计，下跌时长扩大的可能性
        result += '下跌时长 >= ' + str(time) + self.timeUnit + ': ' + str(
            kp2dig(len(trendData[trendData.lastWeeks >= time]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.lastWeeks >= time]) + '\n'

        # 下跌猛烈评判
        result += str(time) + self.timeUnit + '内下跌幅度 <= ' + str(pct) + '%的概率: ' + str(
            kp2dig(len(trendData[trendData.lastWeeks < time][trendData.pct < pct]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.lastWeeks < time][trendData.pct <= pct]) + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

    #对个股的涨跌幅分布的统计
    def volatility(self):
        latitude = max(self.basData.pctChg.max(), abs(self.basData.pctChg.min()))
        latitude = int(latitude) + 1
        statisticData = {'pctChg': [], 'pctChgStr': [], 'num': [], 'percentage':[]}


        for pct in range(-latitude, latitude + 1):
            statisticData['pctChg'].append(pct)
            statisticData['pctChgStr'].append(str(pct) + '-' + str(pct + 1))
            statisticData['num'].append(0)

        for pct in self.basData.pctChg.fillna(0):
            if (pct < 0):
                pct -= 1
            statisticData['num'][int(pct) + latitude] += 1

        length = len(self.basData)
        for i in range(len(statisticData['num'])):
            statisticData['percentage'].append(statisticData['num'][i]/length)

        self.volatilityData = pandas.DataFrame(statisticData)



    def statistic(self):

        self.getBasDat()
        self.getTrendPrd()
        self.getSecondaryTrendData()
        # self.genRisSta()


if __name__ == '__main__':
    use_proxy()

    Index = Share('sh', 'W', '2005-05-18', '2019-09-06')

    # 上证指数的周线系数可用度较高
    Index.setJudgeCondition(1, 2, 6, -1, 2, -6)

    # Index.setJudgeCondition(1, 2, 15, -1, 2, -15)
    Index.statistic()
    #Index.genRisSta()
    #Index.genDownSta()

    Index.genRisTrend(20, 9)
    Index.genDownTrend(-10, 9)
    #Index.volatility()
    #Index.volatilityData.plot.bar(x = 'pctChg', y = 'num')


