"""
计算各类指标，统计其交易成功概率
"""
import os
import pandas as pd
import numpy as numpy

# tools 报错把 外层Helloworld 文件夹 右键 make directory as -> source root
from tools.commom_tools import get_k_data


# 自定义买入条件
from tools.share_analysis import technical_indicators_gen


def up_trade_in(data):
    t = data
    # t = t[t['date'] > '2010-01-01']
    # t = t[t['ma_10'] >= t['ma_60']][t['ma_10'].shift(1) < t['ma_60'].shift(1)]
    t = t[t['close'] >= t['ma_60']]
    t = t[abs(t['pct']) > 4]
    return t.index

# 模拟持股
def trade_out(data, in_index, stop_loss_pct):
    stop_win_pct = 3 * stop_loss_pct
    end_index = max(data.index)
    cost = data['close'].iloc[in_index]
    max_price = cost
    today = in_index + 1
    while today <= end_index:
        # print(data['date'].iloc[today], ' ', data['close'].iloc[today], ' ', data['high'].iloc[today])
        today_close = data['close'].iloc[today]
        today_max = data['high'].iloc[today]

        # 创新高
        if today_max > max_price:
            max_price = today_max

        # 直接止盈
        elif today_close <= cost * (1 - stop_loss_pct):
            # 低于止损价
            return today
        # 过止盈回落，或者从最高点跌落一个止损点，这里有待改进
        elif max_price >= cost * (1 + stop_win_pct):
            if today_close < cost * (1 + stop_win_pct) or today_close < max_price * (1 - stop_loss_pct):
                return today

        # 有一定利润回落至0
        elif max_price >= cost * (1 + stop_loss_pct) and today_close <= cost:
            return today
        today += 1
        # print(max_price, ' ', cost)


def virtual_trade_statics(data, in_function, out_function):
    index = in_function(data)
    origin_index = []
    in_date = []
    out_data = []
    earning_pct = []
    out_index = 1
    for in_index in index:
        if out_index and in_index > out_index:
            out_index = out_function(data, in_index, 0.1)
            if out_index:
                origin_index.append(in_index)
                pct = (data['close'].iloc[out_index] - data['close'].iloc[in_index]) / data['close'].iloc[in_index]
                in_date.append(data['date'].iloc[in_index])
                out_data.append(data['date'].iloc[out_index])
                earning_pct.append(pct)

    t_dict = {'origin_index': origin_index, 'in_date': in_date, 'out_data': out_data, 'earning_pct': earning_pct}
    trade_data = pd.DataFrame(t_dict)
    return trade_data

if __name__ == '__main__':
    # 前复权，不然技术指标没有意义
    data = get_k_data('000725', 'd', 'qfq')
    data = technical_indicators_gen(data)
    t = virtual_trade_statics(data, up_trade_in, trade_out)
