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
        # 从初始数据中提取每周日期，收盘价，涨跌幅
        pd.DataFrame(columns=['date', 'open', 'close', 'pct_chg', 'volume'])
        self.bas_data = self.ori_data_w[['date', 'open', 'close', 'pct_chg', 'volume']]
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
            peak = float(data['close'][peak_index])
            cur = float(data['close'][cur_index])

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
        trend_data = pd.DataFrame(columns=['start_pos', 'end_pos', 'pct', 'last_weeks', 'open', 'close',
                                           'start_w_index', 'end_w_index'])
        # 提取大于3%的涨幅，作为上涨趋势的初期的突破趋势,该幅度可调整
        up_pct_index = data.query('pct_chg > {0} or pct_chg < {1}'.format(self.up_start_pct, self.down_start_pct))

        index = 1
        i = up_pct_index.index[0]
        while i <= self.bas_data.index[-1]:
            end_w_index = self.trend_judge(data, i)

            if end_w_index != i:
                # print('{0},{1},{2},{3}'.format(i,tmp_index,data.date[i],data.date[tmp_index]))
                # 注意是前一周的收盘价，不是当前周的开盘价，涨跌幅都是收盘价算的

                pct = kp2dig(data['close'][end_w_index] / data['open'][i] - 1)
                # print('{0},{1},{2}'.format(beg_price,end_price,pct))

                if ((pct > self.up_pct and end_w_index - i + 1 > self.up_last_times) or
                        (pct < self.down_pct and end_w_index - i + 1 > self.down_last_times)):
                    trend_data.loc[index] = [data.date[i], data.date[end_w_index], pct, end_w_index - i + 1,
                                             data['open'][i],
                                             data['close'][end_w_index], i, end_w_index]
                    i = end_w_index + 1
                    index += 1
                else:
                    i += 1
            else:
                i += 1

        # 调整一下列名顺序，Date_frame创建时列名按字母排序
        order = ['start_pos', 'end_pos', 'pct', 'last_weeks', 'open', 'close', 'start_w_index', 'end_w_index']
        self.trend_data = trend_data

    # 融合的大趋势, 获得次级回调趋势
    def merge_trend_data(self):
        # 取得回调,反弹
        # 次级折返趋势
        trend_data = self.trend_data
        # space_pct折返幅度占之前的比例
        # time_pct折返持续时间占之前的比例

        secondary_trend = {'start_pos': [], 'end_pos': [], 'last_weeks': [], 'pct': [], 'space_pct': [],
                           'time_pct': [], 'open': [], 'close': []}
        secondary_trend = pd.DataFrame(columns=['start_pos', 'end_pos', 'pct', 'last_weeks', 'open', 'close',
                                                'space_pct', 'time_pct'])

        # 合并趋势
        merged_trend = {'start_pos': [], 'end_pos': [], 'pct': [], 'last_weeks': [], 'open': [], 'close': []}
        merged_trend = pd.DataFrame(columns=['start_pos', 'end_pos', 'pct', 'last_weeks', 'open', 'close'])
        up_trend = trend_data[trend_data.pct > 0]
        down_trend = trend_data[trend_data.pct < 0]

        merged_index = 0
        secondary_index = 0

        for trend, judge in zip([up_trend, down_trend], [lambda x, y: x > y, lambda x, y: x < y]):

            first = trend.index[0]
            last = trend.index[0]
            for index in trend.index[1:]:

                if (judge(trend['close'][index], trend['close'][last])
                        and judge(trend['open'][index], trend['open'][last])):
                    # 上行：当前趋势开始和结束都比上一个趋势高，统计下跌时相反
                    secondary_trend.loc[secondary_index] = [trend.end_pos[last], trend.start_pos[index],
                                                            (trend['close'][last] - trend['open'][index]) /
                                                            trend['close'][last],
                                                            trend['start_w_index'][index] - trend['end_w_index'][last],
                                                            trend['close'][last], trend['open'][index],

                                                            (trend['close'][last] - trend['open'][index])
                                                            / (trend['close'][last] - trend['open'][last]),

                                                            (trend['start_w_index'][index] - trend['end_w_index'][
                                                                last]) / trend.last_weeks[last],
                                                            ]
                    last = index
                    secondary_index += 1

                else:
                    merged_trend.loc[merged_index] = [trend.start_pos[first], trend.end_pos[last],
                                                      (trend['close'][last] - trend['open'][first]) / trend['open'][
                                                          first],
                                                      trend['end_w_index'][last] - trend['start_w_index'][
                                                          first] + 1,
                                                      trend['open'][first], trend['close'][last],
                                                      ]
                    merged_index += 1
                    first = index
                    last = index

            # 加最后一个趋势，上面的循环不会处理当前的融合趋势
            merged_trend.loc[merged_index] = [trend.start_pos[first], trend.end_pos[last],
                                              (trend['close'][last] - trend['open'][first]) / trend['open'][first],
                                              trend['end_w_index'][last] - trend['start_w_index'][first] + 1,
                                              trend['open'][first], trend['close'][last],
                                              ]
            merged_index += 1

        # 百分比处理
        for column in ['pct', 'space_pct', 'time_pct']:
            secondary_trend[column] = secondary_trend[column].map(kp2dig)
        merged_trend['pct'] = merged_trend['pct'].map(kp2dig)

        self.secondary_trend = secondary_trend
        self.merged_trend = merged_trend
        # 删除与merged_trend重叠的初始趋势
        drop_list = []
        for i in self.merged_trend.index:
            if not self.merged_trend[
                (self.merged_trend['start_pos'] < self.merged_trend['start_pos'][i]) &
                (self.merged_trend['end_pos'] > self.merged_trend['end_pos'][i])].empty:
                drop_list.append(i)
        self.merged_trend = self.merged_trend.drop(drop_list)

    def gen_up_sta(self):
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

    def gen_trend(self, pct, time):
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
            kp2dig(
                len(trend_data[trend_data.last_weeks < time][trend_data.pct >= pct]) / len(trend_data))) + ' %' + '\n'
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
        t = data['pct_chg'].plot.hist(bins=60)
        t.set_xlim((-11, 11))

    def in_trend(self, index):
        trend = self.merged_trend[(self.merged_trend['start_d_index'] <= index) &
                                  (self.merged_trend['end_d_index'] >= index)]
        # print(trend)
        if trend.empty:
            return -1
        else:
            # 这里index已经不是从0开始的正常顺序了，取0会得到key error
            return trend.index[0]

    def k_line_analysis(self, altitude_l, altitude_u):
        # 用于分析k线在趋势中的位置用
        Mondays = self.merged_trend['start_pos'].map(get_monday)
        self.merged_trend['start_d_index'] = Mondays.map(
            lambda x: self.ori_data_d[self.ori_data_d['date'] >= x].index[0])
        self.merged_trend['end_d_index'] = self.merged_trend['end_pos'].map(
            lambda x: self.ori_data_d[self.ori_data_d['date'] >= x].index[0])

        lines = self.ori_data_d[(self.ori_data_d['pct_chg'].abs() >= altitude_l) &
                                (self.ori_data_d['pct_chg'].abs() < altitude_u)]
        lines['trend_w_index'] = lines.index.map(self.in_trend)
        lines = pd.merge(lines[['date', 'close', 'pct_chg', 'trend_w_index']],
                         self.merged_trend[['start_pos', 'end_pos', 'pct', 'start_d_index', 'end_d_index']],
                         right_index=True, left_on='trend_w_index', how='left')

        # 调试用
        # self.temp_data = lines
        # k线在趋势中的位置
        lines['in_trend_pos'] = lines.index.map(
            lambda x: kp2dig(
                (x - lines['start_d_index'][x]) / (lines['end_d_index'][x] - lines['start_d_index'][x])))
        lines.fillna(0, inplace=True)

        trend_func = {"上行趋势": lambda pct: pct > 0, "下行趋势": lambda pct: pct < 0}
        k_func = {"大涨": lambda x: x > 0, "大跌": lambda x: x < 0}

        print("幅度{}~{}的k线, 占趋势比例".format(altitude_l, altitude_u))
        for trend in trend_func:
            merged_trend = self.merged_trend[trend_func[trend](self.merged_trend['pct'])]
            print('{0}占比约{1:.2f}%'.format(trend,
                                          100 * len(lines[trend_func[trend](lines['pct'])]) / (
                                                  merged_trend['end_d_index'].sum() - merged_trend[
                                              'start_d_index'].sum())))

        _, ax = plt.subplots(2, 2)
        print("k线中各类型占比:")
        for i in range(2):
            for j in range(2):
                trend = ["上行趋势", "下行趋势"][i]
                k_type = ["大涨", "大跌"][j]
                t = lines[trend_func[trend](lines['pct'])][
                    k_func[k_type](lines['pct_chg'])]
                # print(t)
                t['in_trend_pos'].plot(ax=ax[i, j], kind='hist', bins=10)
                ax[i, j].set_title("{}，{}".format(trend, k_type))
                print("{0}，{1} {2:.2f}%".format(trend, k_type,
                                                100 * t['close'].count() / lines['close'].count()))

    def statistic(self):
        self.get_bas_dat()
        self.get_trend_prd()
        self.merge_trend_data()
        # self.gen_up_sta()


if __name__ == '__main__':
    # use_proxy()

    share = Share('sh')
    # 上证指数的周线系数可用度较高
    # share.set_judge_condition(1, 2, 6, -1, 2, -6)
    # share.set_judge_condition(1, 2, 15, -1, 2, -15)
    share.statistic()
    share.gen_trend(20, 9)
    share.gen_down_trend(-10, 9)
    # share.volatility('2014-06-30','2015-05-30')
    # share.k_line_analysis(0, 1)
