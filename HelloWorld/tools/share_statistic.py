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
plt.rcParams['font.sans-serif'] = ['KaiTi']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def use_proxy():
    HTTP_PROXY = "http_proxy"
    HTTPS_PROXY = "https_proxy"
    os.environ[HTTP_PROXY] = "cn-proxy.jp.oracle.com:80"
    os.environ[HTTPS_PROXY] = "cn-proxy.jp.oracle.com:80"
    print(os.environ["http_proxy"])
    print(os.environ["https_proxy"])


def get_and_cache_kDate(code):
    # 获取，并缓存
    if not os.path.exists('data'):
        os.mkdir('data')
    today = datetime.datetime.now().strftime(("%Y-%m-%d"))
    today_folder = "data\\" + today
    if not os.path.exists(today_folder):
        os.mkdir(today_folder)
    if os.path.exists(today_folder + '\\' + code + '_d') and \
            os.path.exists(today_folder + '\\' + code + '_w') and \
            os.path.exists(today_folder + '\\' + code + '_m'):
        print("read from csv")
        ori_data_d = pd.read_csv(today_folder + '\\' + code + '_d')
        ori_data_w = pd.read_csv(today_folder + '\\' + code + '_w')
        ori_data_m = pd.read_csv(today_folder + '\\' + code + '_m')

    else:
        ori_data_m = ts.get_k_data(code, ktype='M', autype='qfq', index=False,
                                 start='2001-01-01', end=today)
        ori_data_w = ts.get_k_data(code, ktype='W', autype='qfq', index=False,
                                 start='2001-01-01', end=today)
        ori_data_d = ts.get_k_data(code, ktype='D', autype='qfq', index=False,
                                 start='2001-01-01', end=today)
        ori_data_d.to_csv(today_folder + '\\' + code + '_d')
        ori_data_w.to_csv(today_folder + '\\' + code + '_w')
        ori_data_m.to_csv(today_folder + '\\' + code + '_m')
    return [ori_data_d, ori_data_w, ori_data_m]


def kp2dig(number):
    # 范围两位小数百分比
    if not np.isnan(number):
        pct = float(number)
        return (int(pct * 10000) / 100.0)
    else:
        return 0


def get_monday(end_pos):
    datetime.date.today()
    end_pos = datetime.datetime.strptime(end_pos, "%Y-%m-%d")
    Monday = end_pos + datetime.timedelta(days=(0 - end_pos.weekday()))
    return Monday.strftime("%Y-%m-%d")


class Share:
    # 上行趋势起始判断涨幅，多少个周期数内未创新稿就结束，涨幅
    up_start_pct = 2
    up_last_times = 4
    up_pct = 10

    down_start_pct = 2
    down_last_times = 4
    down_pct = 10

    def __init__(self, code):
        self.code = code

        # 默认上涨下跌判断条件
        if code == 'sh' or code == 'sz' or code == 'cyb':
            self.set_judge_condition(1, 3, 6, -1, 3, -6)
        else:
            self.set_judge_condition(3, 3, 15, -3, 3, -15)

    def set_judge_condition(self, up_start_pct, up_last_times, up_pct, down_start_pct, down_last_times, down_pct):
        # 上涨，下跌开始判定涨跌比百分率，持续周，合格百分比波动
        # 上涨，下跌微创新低则结束的判定周期次数
        self.up_start_pct = up_start_pct
        self.up_last_times = up_last_times
        self.up_pct = up_pct
        self.down_start_pct = down_start_pct
        self.down_last_times = down_last_times
        self.down_pct = down_pct

    # 获取原始数据self.ori_data, 经过加工的基本数据self.bas_data
    def get_bas_dat(self):
        # 获取原始数据
        self.ori_data_d, self.ori_data_w, self.ori_data_m = get_and_cache_kDate(self.code)

        for data in [self.ori_data_m, self.ori_data_w, self.ori_data_d]:
            data['pct_chg'] = data['close'].pct_change().fillna(0).map(kp2dig)

        self.ori_data_w.index = self.ori_data_w.index - self.ori_data_w.index[0]
        data = self.ori_data_w
        # 从初始数据中提取每周日期，收盘价，涨跌幅
        data_bas = {'date': [], 'open': [], 'close': [], 'pct_chg': [], 'volume': []}
        pct_chg = data['close'].pct_change()
        data_bas['date'].append(data.date[0])
        data_bas['close'].append(float(data.close[0]))
        data_bas['open'].append(float(data.open[0]))
        data_bas['pct_chg'].append(pct_chg[0])
        data_bas['volume'].append(data.volume[0])

        for i in range(len(data) - 1):
            data_bas['date'].append(data.date[i + 1])
            data_bas['close'].append(float(data.close[i + 1]))
            data_bas['open'].append(float(data.open[i + 1]))
            pct = float(pct_chg[i + 1])
            data_bas['pct_chg'].append(kp2dig(pct))
            data_bas['volume'].append(data.volume[i + 1])

        t = pd.DataFrame(data_bas)
        self.bas_data = t.fillna(0)
        return self.bas_data

    # 统计上涨或下跌的趋势维持的时长
    # 返回结束的Index，如果不合格则返回值与输入相同
    def trend_judge(self, data, beg_index):

        begin_pct = data.pct_chg[beg_index]
        cur_index = beg_index
        peak_index = beg_index

        # 确定涨跌
        if begin_pct > 0:
            up_last_times = self.up_last_times
            judge = lambda x, y: x > y

        else:
            up_last_times = self.down_last_times
            judge = lambda x, y: x < y
            self.former_down = beg_index

        week_count = 0
        # 数周内未创新高或新低择视为趋势结束，否则则重新计计数
        while (week_count < up_last_times and cur_index < len(data) - 1):
            cur_index += 1
            peak = float(data.close[peak_index])
            cur = float(data.close[cur_index])

            if judge(cur, peak):
                peak_index = cur_index
                week_count = 0

            else:
                # 未创新高累计周数
                week_count += 1

        return peak_index

    # 从基本数据self.bas_data提取趋势数据 self.trend_data
    def get_trend_prd(self):

        data = self.bas_data

        # 提取上升下降趋势的维持时间，涨幅
        # 开始时间，上升幅度，持续周数
        trend_data = {'start_pos': [], 'end_pos': [], 'pct': [], 'last_weeks': [], 'open': [], 'close': [],
                     'begin_week_index': [], 'end_week_index': []}

        # 提取大于3%的涨幅，作为上涨趋势的初期的突破趋势,该幅度可调整
        ris_pct_index = data.query('pct_chg > ' + str(self.up_start_pct) + ' or pct_chg < ' + str(self.down_start_pct))
        end_week_index = ris_pct_index.index[0] - 1
        i = ris_pct_index.index[0] - 1

        for i in ris_pct_index.index:

            if i <= end_week_index:
                continue

            tmp_index = self.trend_judge(data, i)

            if end_week_index != i:
                # print('{0},{1},{2},{3}'.format(i,tmp_index,data.date[i],data.date[tmp_index]))
                # 注意是前一周的收盘价，不是当前周的开盘价，涨跌幅都是收盘价算的
                beg_price = float(data.close[i - 1])
                end_price = float(data.close[tmp_index])
                pct = kp2dig(end_price / beg_price - 1)
                # print('{0},{1},{2}'.format(beg_price,end_price,pct))

                if pct > self.up_pct or pct < self.down_pct:
                    end_week_index = tmp_index
                    trend_data['start_pos'].append(data.date[i])
                    trend_data['end_pos'].append(data.date[end_week_index])
                    trend_data['pct'].append(pct)
                    trend_data['last_weeks'].append(end_week_index - i + 1)
                    trend_data['open'].append(data.close[i - 1])
                    trend_data['close'].append(data.close[end_week_index])
                    trend_data['begin_week_index'].append(i)
                    trend_data['end_week_index'].append(end_week_index)

        # 调整一下列名顺序，Date_frame创建时列名按字母排序
        order = ['start_pos', 'end_pos', 'pct', 'last_weeks', 'open', 'close', 'begin_week_index', 'end_week_index']
        self.trend_data = pd.DataFrame(trend_data)[order]

    # 获得次级回调趋势，和融合的大趋势
    def get_secondary_trend_data(self):

        trend_data = self.trend_data
        # 取得回调,反弹
        # 次级折返趋势
        # space_pct折返幅度占之前的比例
        # time_pct折返持续时间占之前的比例
        secondary_trend_data = {'start_pos': [], 'end_pos': [], 'last_weeks': [], 'pct': [], 'space_pct': [],
                              'time_pct': [],
                              'open': [], 'close': []}

        # 合并趋势
        merged_trend_data = {'start_pos': [], 'end_pos': [], 'pct': [], 'last_weeks': [], 'open': [], 'close': []}

        ris_trend_data = trend_data[trend_data.pct > 0]
        down_trend_data = trend_data[trend_data.pct < 0]

        # 回调统计
        flag = 0
        for index in ris_trend_data.index:
            if flag == 0:
                # 开始，上一个
                former = index
                last = index
                flag = 1

            elif (ris_trend_data.close[index] > ris_trend_data.close[last]
                  and ris_trend_data.open[index] >= ris_trend_data.open[last]):
                secondary_trend_data['start_pos'].append(ris_trend_data.end_pos[last])
                secondary_trend_data['end_pos'].append(ris_trend_data.start_pos[index])
                secondary_trend_data['last_weeks'].append(
                    ris_trend_data.begin_week_index[index] - ris_trend_data.end_week_index[last])
                secondary_trend_data['pct'].append(
                    kp2dig((ris_trend_data.close[last] - ris_trend_data.close[index]) / ris_trend_data.close[last]))
                secondary_trend_data['space_pct'].append(kp2dig((ris_trend_data.close[last] - ris_trend_data.open[index]) / (
                        ris_trend_data.close[last] - ris_trend_data.open[last])))
                secondary_trend_data['time_pct'].append(kp2dig(
                    (ris_trend_data.begin_week_index[index] - ris_trend_data.end_week_index[last]) / ris_trend_data.last_weeks[
                        last]))
                secondary_trend_data['open'].append(ris_trend_data.close[last])
                secondary_trend_data['close'].append(ris_trend_data.open[index])
                last = index

            else:
                merged_trend_data['start_pos'].append(ris_trend_data.start_pos[former])
                merged_trend_data['end_pos'].append(ris_trend_data.end_pos[last])
                merged_trend_data['last_weeks'].append(
                    ris_trend_data.end_week_index[last] - ris_trend_data.begin_week_index[former])
                merged_trend_data['pct'].append(
                    kp2dig((ris_trend_data.close[last] - ris_trend_data.open[former]) / ris_trend_data.open[former]))
                merged_trend_data['open'].append(ris_trend_data.close[former])
                merged_trend_data['close'].append(ris_trend_data.open[last])
                former = index
                last = index

        # 反弹统计
        flag = 0
        for index in down_trend_data.index:
            if flag == 0:
                former = index
                last = index
                flag = 1

            elif (down_trend_data.close[index] < down_trend_data.close[last]
                  and down_trend_data.open[index] <= down_trend_data.open[last]):
                secondary_trend_data['start_pos'].append(down_trend_data.end_pos[last])
                secondary_trend_data['end_pos'].append(down_trend_data.start_pos[index])
                secondary_trend_data['last_weeks'].append(
                    down_trend_data.begin_week_index[index] - down_trend_data.end_week_index[last])
                secondary_trend_data['pct'].append(
                    kp2dig((down_trend_data.close[last] - down_trend_data.close[index]) / down_trend_data.close[last]))
                secondary_trend_data['space_pct'].append(kp2dig((down_trend_data.close[last] - down_trend_data.open[index]) / (
                        down_trend_data.close[last] - down_trend_data.open[last])))
                secondary_trend_data['time_pct'].append(kp2dig(
                    (down_trend_data.begin_week_index[index] - down_trend_data.end_week_index[last]) / down_trend_data.last_weeks[
                        last]))
                secondary_trend_data['open'].append(down_trend_data.close[last])
                secondary_trend_data['close'].append(down_trend_data.open[index])
                last = index

            else:
                merged_trend_data['start_pos'].append(down_trend_data.start_pos[former])
                merged_trend_data['end_pos'].append(down_trend_data.end_pos[last])
                merged_trend_data['last_weeks'].append(
                    down_trend_data.end_week_index[last] - down_trend_data.begin_week_index[former])
                merged_trend_data['pct'].append(
                    kp2dig((down_trend_data.close[last] - down_trend_data.open[former]) / down_trend_data.open[former]))
                merged_trend_data['open'].append(down_trend_data.open[former])
                merged_trend_data['close'].append(down_trend_data.close[last])
                former = index
                last = index

        self.secondary_trend_data = pd.DataFrame(secondary_trend_data)[
            ['start_pos', 'end_pos', 'pct', 'last_weeks', 'open', 'close', 'space_pct', 'time_pct']]
        self.merged_trend_data = pd.DataFrame(merged_trend_data)[
            ['start_pos', 'end_pos', 'pct', 'last_weeks', 'open', 'close']]

        # 删除merged_trend_data中重叠趋势
        drop_list = []
        for i in self.merged_trend_data.index:
            if not self.merged_trend_data[
                (self.merged_trend_data['start_pos'] < self.merged_trend_data['start_pos'][i]) &
                (self.merged_trend_data['end_pos'] > self.merged_trend_data['end_pos'][i])].empty:
                drop_list.append(i)
        self.merged_trend_data = self.merged_trend_data.drop(drop_list)

        Mondays = self.merged_trend_data['start_pos'].map(get_monday)
        self.merged_trend_data['start_day_index'] = Mondays.map(
            lambda x: self.ori_data_d[self.ori_data_d['date'] >= x].index[0])
        self.merged_trend_data['end_day_index'] = self.merged_trend_data['end_pos'].map(
            lambda x: self.ori_data_d[self.ori_data_d['date'] >= x].index[0])

    def gen_ris_sta(self):
        # 对于上升趋势的总体统计
        data = self.bas_data
        trend_data = self.trend_data[self.trend_data.pct > 0]

        result = ''
        result += '统计时间' + data.date[0] + '~' + data.date[len(data) - 1] + ':\n' + '\n'

        temp_float = 0
        temp_int = 0

        # 综合统计
        # 统计趋势中的超过上涨幅度up_start_pct的k线
        for i in data[data.pct_chg > self.up_start_pct].index:
            if len(trend_data[trend_data.start_pos < data.date[i]][trend_data.end_pos > data.date[i]]) > 0:
                temp_int += 1
        temp_float = kp2dig(len(trend_data) / (len(data[data.pct_chg > self.up_start_pct]) - temp_int))

        result += '上涨百分比 >= ' + str(self.up_start_pct) + '% 的k线共 ' + str(
            len(data[data.pct_chg > self.up_start_pct])) + ' 个' + '\n'
        result += '其中形成趋势的有 ' + str(len(trend_data)) + ' 个k线' + '\n'
        result += '去除上涨趋势中的 ' + str(temp_int) + ' 条k线，形成趋势概率' + str(temp_float) + '%' + '\n' + '\n'
        result += '平均上涨幅度: ' + str(kp2dig(trend_data.pct.mean() / 100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(trend_data.last_weeks.mean() / 100)) + "周" + '\n' + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

    def gen_ris_trend(self, pct, time):
        # 涨幅大于pct大概率 和时长大于time的概率
        trend_data = self.trend_data[self.trend_data.pct > 0]

        result = '形成的趋势中'

        # 根据统计，上涨幅度增加的可能性
        result += '上涨幅度 >= ' + str(pct) + '% 的概率: ' + str(
            kp2dig(len(trend_data[trend_data.pct >= pct]) / len(trend_data))) + ' %' + '\n'
        result += str(trend_data[trend_data.pct >= pct]) + '\n'

        # 根据统计，上涨时长增加的可能性
        result += '上涨时长 >= ' + str(time) + "周" + ': ' + str(
            kp2dig(len(trend_data[trend_data.last_weeks >= time]) / len(trend_data))) + ' %' + '\n'
        result += str(trend_data[trend_data.last_weeks >= time]) + '\n'

        # 上涨猛烈程度评判
        result += str(time) + "周" + '内上涨幅度 >= ' + str(pct) + '%的概率: ' + str(
            kp2dig(len(trend_data[trend_data.last_weeks < time][trend_data.pct >= pct]) / len(trend_data))) + ' %' + '\n'
        result += str(trend_data[trend_data.last_weeks < time][trend_data.pct > pct]) + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

    def gen_down_sta(self):
        data = self.bas_data
        trend_data = self.trend_data[self.trend_data.pct < 0]

        # 对于上升趋势的总体统计

        result = ''
        result += '统计时间' + data.date[0] + '~' + data.date[len(data) - 1] + ':\n' + '\n'

        temp_float = 0
        temp_int = 0

        # 趋势综合统计
        # 统计趋势中的超过上涨幅度up_start_pct的k线（下行相反）
        for i in data[data.pct_chg < self.down_start_pct].index:
            if len(trend_data[trend_data.start_pos < data.date[i]][trend_data.end_pos > data.date[i]]) > 0:
                temp_int += 1
        temp_float = kp2dig(len(trend_data) / (len(data[data.pct_chg < self.down_start_pct]) - temp_int))

        result += '下跌百分比 <= ' + str(self.down_start_pct) + '% 的k线共 ' + str(
            len(data[data.pct_chg < self.down_start_pct])) + ' 个' + '\n'
        result += '其中形成下跌趋势的有 ' + str(len(trend_data)) + ' 个k线' + '\n'
        result += '去除下跌趋势中的 ' + str(temp_int) + ' 条k线，形成趋势概率' + str(temp_float) + '%' + '\n' + '\n'
        result += '平均下跌幅度: ' + str(kp2dig(trend_data.pct.mean() / 100)) + ' %' + '\n'
        result += '平均维持时长: ' + str(kp2dig(trend_data.last_weeks.mean() / 100)) + "周" + '\n' + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

    def gen_down_trend(self, pct, time):
        # 跌幅大于pct大概率 和时长大于time的概率
        trend_data = self.trend_data[self.trend_data.pct < 0]
        result = '形成的趋势中'

        # 根据统计，下跌幅度扩大的可能性
        result += '幅度:下跌幅度 <= ' + str(pct) + '% 的概率: ' + str(
            kp2dig(len(trend_data[trend_data.pct <= pct]) / len(trend_data))) + ' %' + '\n'
        result += str(trend_data[trend_data.pct < pct]) + '\n'

        # 根据统计，下跌时长扩大的可能性
        result += '下跌时长 >= ' + str(time) + "周" + ': ' + str(
            kp2dig(len(trend_data[trend_data.last_weeks >= time]) / len(trend_data))) + ' %' + '\n'
        result += str(trend_data[trend_data.last_weeks >= time]) + '\n'

        # 下跌猛烈评判
        result += str(time) + "周" + '内下跌幅度 <= ' + str(pct) + '%的概率: ' + str(
            kp2dig(len(trend_data[trend_data.last_weeks < time][trend_data.pct < pct]) / len(trend_data))) + ' %' + '\n'
        result += str(trend_data[trend_data.last_weeks < time][trend_data.pct <= pct]) + '\n'

        print('-------------------------------------------------------------------------------')
        print(result)

        # 对个股的涨跌幅频率分布的统计

    def volatility(self, start_date=None, end_date=None):
        data = self.bas_data
        if start_date:
            data = data[self.bas_data['date'] >= start_date]
        if end_date:
            data = data[self.bas_data['date'] <= end_date]

        # 改为使用聚合函数
        group_names = ["{}-{}".format(left, right) for left, right in zip(range(-10, 10), range(-9, 11))]
        cuts = pd.cut(data['pct_chg'], range(-10, 11), labels=group_names)
        self.volatility_data = pd.value_counts(cuts)

        # 绘制频率统计图
        data['pct_chg'].plot.hist(bins=60)

        # 某个日期所在的趋势

    def in_trend(self, index):
        trend = self.merged_trend_data[(self.merged_trend_data['start_day_index'] <= index) &
                                     (self.merged_trend_data['end_day_index'] >= index)]
        # print(trend)
        if trend.empty:
            return -1
        else:
            # 这里index已经不是从0开始的正常顺序了，取0会得到key error
            return trend.index[0]

    def k_line_analysis(self, altitude_l, altitude_u):
        lines = self.ori_data_d[(self.ori_data_d['pct_chg'].abs() >= altitude_l) &
                              (self.ori_data_d['pct_chg'].abs() < altitude_u)]
        lines['trend_week_index'] = lines.index.map(self.in_trend)
        lines = pd.merge(lines[['date', 'close', 'pct_chg', 'trend_week_index']],
                         self.merged_trend_data[['start_pos', 'end_pos', 'pct', 'start_day_index', 'end_day_index']],
                         right_index=True, left_on='trend_week_index', how='left')

        # 调试用
        self.temp_data = lines
        # k线在趋势中的位置
        lines['in_trend_pos'] = lines.index.map(
            lambda x: kp2dig((x - lines['start_day_index'][x]) / (lines['end_day_index'][x] - lines['start_day_index'][x])))

        print("幅度{}~{}的k线, 占趋势比例".format(altitude_l, altitude_u))
        ris_merged_trend = self.merged_trend_data[self.merged_trend_data['pct'] > 0]
        down_merged_trend = self.merged_trend_data[self.merged_trend_data['pct'] < 0]
        print('所有趋势占比约{0:.2f}%'.format(
            100 * len(lines[lines['trend_week_index'] != -1]) / (
                    self.merged_trend_data['end_day_index'].sum() - self.merged_trend_data['start_day_index'].sum())))
        print('上行趋势占比约{0:.2f}%'.format(
            100 * len(lines[lines['pct'] > 0]) / (
                    ris_merged_trend['end_day_index'].sum() - ris_merged_trend['start_day_index'].sum())))
        print('下行趋势占比约{0:.2f}%'.format(
            100 * len(lines[lines['pct'] < 0]) / (
                    down_merged_trend['end_day_index'].sum() - down_merged_trend['start_day_index'].sum())))

        _, ax = plt.subplots(2, 2)
        print("k线中各类型占比:")
        # lines[lines['pct'] > 0][lines['pct_chg'] > 0]['in_trend_pos'].plot(subplots=(2, 2, 2), kind='hist', bins=50)
        t = lines['in_trend_pos'][lines['pct'] > 0][lines['pct_chg'] > 0]
        t.plot(ax=ax[0, 0], kind='hist', bins=10)
        ax[0, 0].set_title("上行，大阳")
        print("上行，大阳 {0:.2f}%".format(
            100 * t.count() / lines['close'].count()))

        t = lines['in_trend_pos'][lines['pct'] > 0][lines['pct_chg'] < 0]
        t.plot(ax=ax[0, 1], kind='hist', bins=10)
        ax[0, 1].set_title("上行，大阴")
        print("上行，大阴 {0:.2f}%".format(
            100 * t.count() / lines['close'].count()))

        t = lines['in_trend_pos'][lines['pct'] < 0][lines['pct_chg'] > 0]
        t.plot(ax=ax[1, 0], kind='hist', bins=10)
        ax[1, 0].set_title("下跌，大阳")
        print("下跌，大阳 {0:.2f}%".format(
            100 * t.count() / lines['close'].count()))

        t = lines['in_trend_pos'][lines['pct'] < 0][lines['pct_chg'] < 0]
        t.plot(ax=ax[1, 1], kind='hist', bins=10)
        ax[1, 1].set_title("下跌，大阴")
        print("下跌，大阴 {0:.2f}%".format(
            100 * t.count() / lines['close'].count()))

        print("无趋势，大阳 {0:.2f}%".format(
            100 * lines['close'][lines['trend_week_index'] == -1][lines['pct_chg'] > 0].count() / lines['close'].count()))
        print("无趋势，大阴 {0:.2f}%".format(
            100 * lines['close'][lines['trend_week_index'] == -1][lines['pct_chg'] < 0].count() / lines['close'].count()))
        return lines

    def statistic(self):
        self.get_bas_dat()
        self.get_trend_prd()
        self.get_secondary_trend_data()
        # self.gen_ris_sta()


if __name__ == '__main__':
    # use_proxy()

    share = Share('sh')
    # 上证指数的周线系数可用度较高
    # share.set_judge_condition(1, 2, 6, -1, 2, -6)
    # share.set_judge_condition(1, 2, 15, -1, 2, -15)
    share.statistic()
    share.gen_ris_trend(20, 9)
    share.gen_down_trend(-10, 9)
    # share.volatility('2014-06-30','2015-05-30')
    # share.k_line_analysis(0, 1)
