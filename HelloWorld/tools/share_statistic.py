# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import datetime
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tushare as ts

# 支持中文
plt.rcParams['font.sans-serif'] = ['KaiTi']
plt.rcParams['axes.unicode_minus'] = False


def use_proxy():
    HTTP_PROXY = "http_proxy"
    HTTPS_PROXY = "https_proxy"
    os.environ[HTTP_PROXY] = "cn-proxy.jp.oracle.com:80"
    os.environ[HTTPS_PROXY] = "cn-proxy.jp.oracle.com:80"
    print(os.environ["http_proxy"])
    print(os.environ["https_proxy"])


def getAndCacheKDate(code):
    # 获取，并缓存
    if not os.path.exists('data'):
        os.mkdir('data')
    today = datetime.datetime.now().strftime(("%Y-%m-%d"))
    todayFolder = "data\\" + today
    if not os.path.exists(todayFolder):
        os.mkdir(todayFolder)
    if os.path.exists(todayFolder + '\\' + code + '_d') and \
            os.path.exists(todayFolder + '\\' + code + '_w') and \
            os.path.exists(todayFolder + '\\' + code + '_m'):
        print("read from csv")
        oriDataD = pd.read_csv(todayFolder + '\\' + code + '_d')
        oriDataW = pd.read_csv(todayFolder + '\\' + code + '_w')
        oriDataM = pd.read_csv(todayFolder + '\\' + code + '_m')

    else:
        oriDataM = ts.get_k_data(code, ktype='M', autype='qfq', index=False,
                                 start='2001-01-01', end=today)
        oriDataW = ts.get_k_data(code, ktype='W', autype='qfq', index=False,
                                 start='2001-01-01', end=today)
        oriDataD = ts.get_k_data(code, ktype='D', autype='qfq', index=False,
                                 start='2001-01-01', end=today)
        oriDataD.to_csv(todayFolder + '\\' + code + '_d')
        oriDataW.to_csv(todayFolder + '\\' + code + '_w')
        oriDataM.to_csv(todayFolder + '\\' + code + '_m')
    return [oriDataD, oriDataW, oriDataM]


def kp2dig(number):
    # 范围两位小数百分比
    if not np.isnan(number):
        pct = float(number)
        return (int(pct * 10000) / 100.0)
    else:
        return 0


def getMonday(endPos):
    datetime.date.today()
    endPos = datetime.datetime.strptime(endPos, "%Y-%m-%d")
    Monday = endPos + datetime.timedelta(days=(0 - endPos.weekday()))
    return Monday.strftime("%Y-%m-%d")


class Share:
    # 上行趋势起始判断涨幅，多少个周期数内未创新稿就结束，涨幅
    upStartPct = 2
    upLastTimes = 4
    upPct = 10

    downStartPct = 2
    downLastTimes = 4
    downPct = 10

    def __init__(self, code):
        self.code = code

        # 默认上涨下跌判断条件
        if code == 'sh' or code == 'sz' or code == 'cyb':
            self.setJudgeCondition(1, 3, 6, -1, 3, -6)
        else:
            self.setJudgeCondition(3, 3, 15, -3, 3, -15)

    def setJudgeCondition(self, upStartPct, upLastTimes, upPct, downStartPct, downLastTimes, downPct):
        # 上涨，下跌开始判定涨跌比百分率，持续周，合格百分比波动
        # 上涨，下跌微创新低则结束的判定周期次数
        self.upStartPct = upStartPct
        self.upLastTimes = upLastTimes
        self.upPct = upPct
        self.downStartPct = downStartPct
        self.downLastTimes = downLastTimes
        self.downPct = downPct

    # 获取原始数据self.oriData, 经过加工的基本数据self.basData
    def getBasDat(self):
        # 获取原始数据
        self.oriDataD, self.oriDataW, self.oriDataM = getAndCacheKDate(self.code)

        for data in [self.oriDataM, self.oriDataW, self.oriDataD]:
            data['pctChg'] = data['close'].pct_change().fillna(0).map(kp2dig)

        self.oriDataW.index = self.oriDataW.index - self.oriDataW.index[0]
        data = self.oriDataW
        # 从初始数据中提取每周日期，收盘价，涨跌幅
        dataBas = {'date': [], 'open': [], 'close': [], 'pctChg': [], 'volume': []}
        pctChg = data['close'].pct_change()
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

        t = pd.DataFrame(dataBas)
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
        # 数周内未创新高或新低择视为趋势结束，否则则重新计计数
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

    # 从基本数据self.basData提取趋势数据 self.trendData
    def getTrendPrd(self):

        data = self.basData

        # 提取上升下降趋势的维持时间，涨幅
        # 开始时间，上升幅度，持续周数
        trendData = {'startPos': [], 'endPos': [], 'pct': [], 'lastWeeks': [], 'open': [], 'close': [],
                     'beginWeekIndex': [], 'endWeekIndex': []}

        # 提取大于3%的涨幅，作为上涨趋势的初期的突破趋势,该幅度可调整
        ris_pct_index = data.query('pctChg > ' + str(self.upStartPct) + ' or pctChg < ' + str(self.downStartPct))
        endWeekIndex = ris_pct_index.index[0] - 1
        i = ris_pct_index.index[0] - 1

        for i in ris_pct_index.index:

            if i <= endWeekIndex:
                continue

            tmpIndex = self.trendJudge(data, i)

            if endWeekIndex != i:
                # print('{0},{1},{2},{3}'.format(i,tmpIndex,data.date[i],data.date[tmpIndex]))
                # 注意是前一周的收盘价，不是当前周的开盘价，涨跌幅都是收盘价算的
                begPrice = float(data.close[i - 1])
                endPrice = float(data.close[tmpIndex])
                pct = kp2dig(endPrice / begPrice - 1)
                # print('{0},{1},{2}'.format(begPrice,endPrice,pct))

                if pct > self.upPct or pct < self.downPct:
                    endWeekIndex = tmpIndex
                    trendData['startPos'].append(data.date[i])
                    trendData['endPos'].append(data.date[endWeekIndex])
                    trendData['pct'].append(pct)
                    trendData['lastWeeks'].append(endWeekIndex - i + 1)
                    trendData['open'].append(data.close[i - 1])
                    trendData['close'].append(data.close[endWeekIndex])
                    trendData['beginWeekIndex'].append(i)
                    trendData['endWeekIndex'].append(endWeekIndex)

        # 调整一下列名顺序，DateFrame创建时列名按字母排序
        order = ['startPos', 'endPos', 'pct', 'lastWeeks', 'open', 'close', 'beginWeekIndex', 'endWeekIndex']
        self.trendData = pd.DataFrame(trendData)[order]

    # 获得次级回调趋势，和融合的大趋势
    def getSecondaryTrendData(self):

        trendData = self.trendData
        # 取得回调,反弹
        # 次级折返趋势
        # spacePct折返幅度占之前的比例
        # timePct折返持续时间占之前的比例
        secondaryTrendData = {'startPos': [], 'endPos': [], 'lastWeeks': [], 'pct': [], 'spacePct': [],
                              'timePct': [],
                              'open': [], 'close': []}

        # 合并趋势
        mergedTrendData = {'startPos': [], 'endPos': [], 'pct': [], 'lastWeeks': [], 'open': [], 'close': []}

        risTrendData = trendData[trendData.pct > 0]
        downTrendData = trendData[trendData.pct < 0]

        # 回调统计
        flag = 0
        for index in risTrendData.index:
            if flag == 0:
                # 开始，上一个
                former = index
                last = index
                flag = 1

            elif (risTrendData.close[index] > risTrendData.close[last]
                  and risTrendData.open[index] >= risTrendData.open[last]):
                secondaryTrendData['startPos'].append(risTrendData.endPos[last])
                secondaryTrendData['endPos'].append(risTrendData.startPos[index])
                secondaryTrendData['lastWeeks'].append(
                    risTrendData.beginWeekIndex[index] - risTrendData.endWeekIndex[last])
                secondaryTrendData['pct'].append(
                    kp2dig((risTrendData.close[last] - risTrendData.close[index]) / risTrendData.close[last]))
                secondaryTrendData['spacePct'].append(kp2dig((risTrendData.close[last] - risTrendData.open[index]) / (
                        risTrendData.close[last] - risTrendData.open[last])))
                secondaryTrendData['timePct'].append(kp2dig(
                    (risTrendData.beginWeekIndex[index] - risTrendData.endWeekIndex[last]) / risTrendData.lastWeeks[
                        last]))
                secondaryTrendData['open'].append(risTrendData.close[last])
                secondaryTrendData['close'].append(risTrendData.open[index])
                last = index

            else:
                mergedTrendData['startPos'].append(risTrendData.startPos[former])
                mergedTrendData['endPos'].append(risTrendData.endPos[last])
                mergedTrendData['lastWeeks'].append(
                    risTrendData.endWeekIndex[last] - risTrendData.beginWeekIndex[former])
                mergedTrendData['pct'].append(
                    kp2dig((risTrendData.close[last] - risTrendData.open[former]) / risTrendData.open[former]))
                mergedTrendData['open'].append(risTrendData.close[former])
                mergedTrendData['close'].append(risTrendData.open[last])
                former = index
                last = index

        # 反弹统计
        flag = 0
        for index in downTrendData.index:
            if flag == 0:
                former = index
                last = index
                flag = 1

            elif (downTrendData.close[index] < downTrendData.close[last]
                  and downTrendData.open[index] <= downTrendData.open[last]):
                secondaryTrendData['startPos'].append(downTrendData.endPos[last])
                secondaryTrendData['endPos'].append(downTrendData.startPos[index])
                secondaryTrendData['lastWeeks'].append(
                    downTrendData.beginWeekIndex[index] - downTrendData.endWeekIndex[last])
                secondaryTrendData['pct'].append(
                    kp2dig((downTrendData.close[last] - downTrendData.close[index]) / downTrendData.close[last]))
                secondaryTrendData['spacePct'].append(kp2dig((downTrendData.close[last] - downTrendData.open[index]) / (
                        downTrendData.close[last] - downTrendData.open[last])))
                secondaryTrendData['timePct'].append(kp2dig(
                    (downTrendData.beginWeekIndex[index] - downTrendData.endWeekIndex[last]) / downTrendData.lastWeeks[
                        last]))
                secondaryTrendData['open'].append(downTrendData.close[last])
                secondaryTrendData['close'].append(downTrendData.open[index])
                last = index

            else:
                mergedTrendData['startPos'].append(downTrendData.startPos[former])
                mergedTrendData['endPos'].append(downTrendData.endPos[last])
                mergedTrendData['lastWeeks'].append(
                    downTrendData.endWeekIndex[last] - downTrendData.beginWeekIndex[former])
                mergedTrendData['pct'].append(
                    kp2dig((downTrendData.close[last] - downTrendData.open[former]) / downTrendData.open[former]))
                mergedTrendData['open'].append(downTrendData.open[former])
                mergedTrendData['close'].append(downTrendData.close[last])
                former = index
                last = index

        self.secondaryTrendData = pd.DataFrame(secondaryTrendData)[
            ['startPos', 'endPos', 'pct', 'lastWeeks', 'open', 'close', 'spacePct', 'timePct']]
        self.mergedTrendData = pd.DataFrame(mergedTrendData)[
            ['startPos', 'endPos', 'pct', 'lastWeeks', 'open', 'close']]

        # 删除mergedTrendData中重叠趋势
        dropList = []
        for i in self.mergedTrendData.index:
            if not self.mergedTrendData[
                (self.mergedTrendData['startPos'] < self.mergedTrendData['startPos'][i]) &
                (self.mergedTrendData['endPos'] > self.mergedTrendData['endPos'][i])].empty:
                dropList.append(i)
        self.mergedTrendData = self.mergedTrendData.drop(dropList)

        Mondays = self.mergedTrendData['startPos'].map(getMonday)
        self.mergedTrendData['startDayIndex'] = Mondays.map(
            lambda x: self.oriDataD[self.oriDataD['date'] >= x].index[0])
        self.mergedTrendData['endDayIndex'] = self.mergedTrendData['endPos'].map(
            lambda x: self.oriDataD[self.oriDataD['date'] >= x].index[0])

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
            if len(trendData[trendData.startPos < data.date[i]][trendData.endPos > data.date[i]]) > 0:
                tempInt += 1
        tempFloat = kp2dig(len(trendData) / (len(data[data.pctChg > self.upStartPct]) - tempInt))

        result += '上涨百分比 >= ' + str(self.upStartPct) + '% 的k线共 ' + str(
            len(data[data.pctChg > self.upStartPct])) + ' 个' + '\n'
        result += '其中形成趋势的有 ' + str(len(trendData)) + ' 个k线' + '\n'
        result += '去除上涨趋势中的 ' + str(tempInt) + ' 条k线，形成趋势概率' + str(tempFloat) + '%' + '\n' + '\n'
        result += '平均上涨幅度: ' + str(kp2dig(trendData.pct.mean() / 100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(trendData.lastWeeks.mean() / 100)) + "周" + '\n' + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

    def genRisTrend(self, pct, time):
        # 涨幅大于pct大概率 和时长大于time的概率
        trendData = self.trendData[self.trendData.pct > 0]

        result = '形成的趋势中'

        # 根据统计，上涨幅度增加的可能性
        result += '上涨幅度 >= ' + str(pct) + '% 的概率: ' + str(
            kp2dig(len(trendData[trendData.pct >= pct]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.pct >= pct]) + '\n'

        # 根据统计，上涨时长增加的可能性
        result += '上涨时长 >= ' + str(time) + "周" + ': ' + str(
            kp2dig(len(trendData[trendData.lastWeeks >= time]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.lastWeeks >= time]) + '\n'

        # 上涨猛烈程度评判
        result += str(time) + "周" + '内上涨幅度 >= ' + str(pct) + '%的概率: ' + str(
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
            if len(trendData[trendData.startPos < data.date[i]][trendData.endPos > data.date[i]]) > 0:
                tempInt += 1
        tempFloat = kp2dig(len(trendData) / (len(data[data.pctChg < self.downStartPct]) - tempInt))

        result += '下跌百分比 <= ' + str(self.downStartPct) + '% 的k线共 ' + str(
            len(data[data.pctChg < self.downStartPct])) + ' 个' + '\n'
        result += '其中形成下跌趋势的有 ' + str(len(trendData)) + ' 个k线' + '\n'
        result += '去除下跌趋势中的 ' + str(tempInt) + ' 条k线，形成趋势概率' + str(tempFloat) + '%' + '\n' + '\n'
        result += '平均下跌幅度: ' + str(kp2dig(trendData.pct.mean() / 100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(trendData.lastWeeks.mean() / 100)) + "周" + '\n' + '\n'

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
        result += '下跌时长 >= ' + str(time) + "周" + ': ' + str(
            kp2dig(len(trendData[trendData.lastWeeks >= time]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.lastWeeks >= time]) + '\n'

        # 下跌猛烈评判
        result += str(time) + "周" + '内下跌幅度 <= ' + str(pct) + '%的概率: ' + str(
            kp2dig(len(trendData[trendData.lastWeeks < time][trendData.pct < pct]) / len(trendData))) + ' %' + '\n'
        result += str(trendData[trendData.lastWeeks < time][trendData.pct <= pct]) + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

        # 对个股的涨跌幅频率分布的统计

    def volatility(self, startDate=None, endDate=None):
        data = self.basData
        if startDate:
            data = data[self.basData['date'] >= startDate]
        if endDate:
            data = data[self.basData['date'] <= endDate]

        # 改为使用聚合函数
        group_names = ["{}-{}".format(left, right) for left, right in zip(range(-10, 10), range(-9, 11))]
        cuts = pd.cut(data['pctChg'], range(-10, 11), labels=group_names)
        self.volatilityData = pd.value_counts(cuts)

        # 绘制频率统计图
        data['pctChg'].plot.hist(bins=60)

        # 某个日期所在的趋势

    def in_trend(self, index):
        trend = self.mergedTrendData[(self.mergedTrendData['startDayIndex'] <= index) &
                                     (self.mergedTrendData['endDayIndex'] >= index)]
        # print(trend)
        if trend.empty:
            return -1
        else:
            # 这里index已经不是从0开始的正常顺序了，取0会得到key error
            return trend.index[0]

    def kLineAnalysis(self, altitude_l, altitude_u):
        lines = self.oriDataD[(self.oriDataD['pctChg'].abs() >= altitude_l) &
                              (self.oriDataD['pctChg'].abs() < altitude_u)]
        lines['trendWeekIndex'] = lines.index.map(self.in_trend)
        lines = pd.merge(lines[['date', 'close', 'pctChg', 'trendWeekIndex']],
                         self.mergedTrendData[['startPos', 'endPos', 'pct', 'startDayIndex', 'endDayIndex']],
                         right_index=True, left_on='trendWeekIndex', how='left')

        # 调试用
        self.tempData = lines
        # k线在趋势中的位置
        lines['inTrendPos'] = lines.index.map(
            lambda x: kp2dig((x - lines['startDayIndex'][x]) / (lines['endDayIndex'][x] - lines['startDayIndex'][x])))

        print("幅度{}~{}的k线, 占趋势比例".format(altitude_l, altitude_u))
        risMergedTrend = self.mergedTrendData[self.mergedTrendData['pct'] > 0]
        downMergedTrend = self.mergedTrendData[self.mergedTrendData['pct'] < 0]
        print('所有趋势占比约{0:.2f}%'.format(
            100 * len(lines[lines['trendWeekIndex'] != -1]) / (
                    self.mergedTrendData['endDayIndex'].sum() - self.mergedTrendData['startDayIndex'].sum())))
        print('上行趋势占比约{0:.2f}%'.format(
            100 * len(lines[lines['pct'] > 0]) / (
                    risMergedTrend['endDayIndex'].sum() - risMergedTrend['startDayIndex'].sum())))
        print('下行趋势占比约{0:.2f}%'.format(
            100 * len(lines[lines['pct'] < 0]) / (
                    downMergedTrend['endDayIndex'].sum() - downMergedTrend['startDayIndex'].sum())))

        _, ax = plt.subplots(2, 2)
        print("k线中各类型占比:")
        # lines[lines['pct'] > 0][lines['pctChg'] > 0]['inTrendPos'].plot(subplots=(2, 2, 2), kind='hist', bins=50)
        t = lines['inTrendPos'][lines['pct'] > 0][lines['pctChg'] > 0]
        t.plot(ax=ax[0, 0], kind='hist', bins=10)
        ax[0, 0].set_title("上行，大阳")
        print("上行，大阳 {0:.2f}%".format(
            100 * t.count() / lines['close'].count()))

        t = lines['inTrendPos'][lines['pct'] > 0][lines['pctChg'] < 0]
        t.plot(ax=ax[0, 1], kind='hist', bins=10)
        ax[0, 1].set_title("上行，大阴")
        print("上行，大阴 {0:.2f}%".format(
            100 * t.count() / lines['close'].count()))

        t = lines['inTrendPos'][lines['pct'] < 0][lines['pctChg'] > 0]
        t.plot(ax=ax[1, 0], kind='hist', bins=10)
        ax[1, 0].set_title("下跌，大阳")
        print("下跌，大阳 {0:.2f}%".format(
            100 * t.count() / lines['close'].count()))

        t = lines['inTrendPos'][lines['pct'] < 0][lines['pctChg'] < 0]
        t.plot(ax=ax[1, 1], kind='hist', bins=10)
        ax[1, 1].set_title("下跌，大阴")
        print("下跌，大阴 {0:.2f}%".format(
            100 * t.count() / lines['close'].count()))

        print("无趋势，大阳 {0:.2f}%".format(
            100 * lines['close'][lines['trendWeekIndex'] == -1][lines['pctChg'] > 0].count() / lines['close'].count()))
        print("无趋势，大阴 {0:.2f}%".format(
            100 * lines['close'][lines['trendWeekIndex'] == -1][lines['pctChg'] < 0].count() / lines['close'].count()))
        return lines

    def statistic(self):
        self.getBasDat()
        self.getTrendPrd()
        self.getSecondaryTrendData()
        # self.genRisSta()


if __name__ == '__main__':
    # use_proxy()

    share = Share('sh')
    # 上证指数的周线系数可用度较高
    # share.setJudgeCondition(1, 2, 6, -1, 2, -6)
    # share.setJudgeCondition(1, 2, 15, -1, 2, -15)
    share.statistic()
    share.genRisTrend(20, 9)
    share.genDownTrend(-10, 9)
    # share.volatility('2014-06-30','2015-05-30')
    # share.kLineAnalysis(0, 1)
