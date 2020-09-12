"""
计算各类指标，统计其交易成功概率
"""
import os
import pandas as pd

# 由于tushare的前复权数据有严重计算错误问题，这里考虑直接手动从东方财富后台拉数据
# 一般而言打开日k后，后台传输数据最大的就是日k，url一般是js?token=....
# 点开响应，等待片刻，复制其中data的数据，保存为[..]格式，文件名为股票代码

# tools 报错把 外层Helloworld 文件夹 右键 make directory as -> source root
from tools.commom_tools import get_k_data


def data_process(code):
    path = 'data/{}'.format(code)
    if os.path.exists(path + '.csv'):
        return pd.read_csv(path + '.csv')
    elif os.path.exists(path):
        with open(path) as f:
            # 读进来的是个列表字符
            raw_data = eval(f.read())

        columns = ['date', 'open', 'close', 'high', 'low', 'number', 'volume', 'turnover_rate']
        pd_data = {c: [] for c in columns}

        for line in raw_data:
            t_data = line.split(',')
            for i in range(len(columns)):
                pd_data[columns[i]].append(t_data[i])

        ans = pd.DataFrame(pd_data)
        # 把换手率从字符转为数字
        ans['turnover_rate'] = ans['turnover_rate'].replace('-', '0%')
        ans['turnover_rate'] = ans['turnover_rate'].map(lambda p: float(p.replace('%', '')))

        for c in ['open', 'close', 'high', 'low', 'number', 'volume']:
            ans[c] = ans[c].map(float)
        ans['pct'] = ans['close'].pct_change().fillna(0) * 100

        ans.to_csv(path + '.csv')
        return ans
    else:
        raise Exception("文件没下载")


def data_retreatment(data):
    # 注意股价不能前移，否则就是未来函数

    # 当要比较数值与均价的关系时，用 MA 就可以了，而要比较均价的趋势快慢时，用 EMA 更稳定
    # 均线ma
    for n in [20, 60, 200]:
        data['ma_{}'.format(n)] = data['close'].rolling(n).mean()

    # MACD
    # 先计算ema，α=2/(span+1), adjust=False 采用递推式计算，而不是整体计算
    ema_12 = data['close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['close'].ewm(span=26, adjust=False).mean()
    data['dif'] = ema_12 - ema_26
    data['dea'] = data['dif'].ewm(span=9, adjust=False).mean()
    data['macd'] = (data['dif'] - data['dea']) * 2

    # obv统计成交量变动的趋势来推测股价趋势, 逐日累计每日上市股票总成交量，若上涨，加，下跌，减
    data['obv'] = (data['pct'].map(lambda x: 1 if x > 0 else -1) * data['volume']).cumsum()

    #  RSV指标主要用来分析市场是处于“超买”还是“超卖”：RSV高于80%时候市场即为超买；RSV低于20%时候，市场为超卖
    #  rsv =(收盘价 – n日内最低价)/(n日内最高价 – n日内最低价)×100
    t_min = data['low'].rolling(24).min()
    t_max = data['high'].rolling(24).max()
    data['rsv_24'] = (data['close'] - t_min) / (t_max - t_min) * 100
    # 当日K值=2/3×前一日K值+1/3×当日RSV
    #  α=1/(1+com)
    data['k'] = data['rsv_24'].ewm(com=2, adjust=False).mean()
    # 当日D值 = 2 / 3×前一日D值 + 1 / 3×当日K值
    data['d'] = data['k'].ewm(com=2, adjust=False).mean()
    # J值 = 3 * 当日K值 - 2 * 当日D值
    data['j'] = 3 * data['k'] - 2 * data['d']

    # rsi
    # 方法1：rsi = A/（A + B）×100, A——N日内收盘涨幅之和, B——N日内收盘跌幅之和(取正值)
    dif = data['close'].diff(1)
    ris_close = dif.map(lambda x: x if x > 0 else 0)
    down_close = dif.map(lambda x: -x if x < 0 else 0)
    for n in [12, 24, 48]:
        a = ris_close.rolling(n).sum()
        b = down_close.rolling(n).sum()
        data['rsi_{}'.format(n)] = a / (a + b) * 100

    # bolling 线
    ma = data['close'].rolling(20).mean()
    md = data['close'].rolling(20).std()  # ddof代表标准差自由度
    # 计算上轨、下轨道
    data['bolling_upper'] = ma + 2 * md
    data['bolling_lower'] = ma - 2 * md

    # 乖离率
    # BIAS=(收盘价-收盘价的N日简单平均)/收盘价的N日简单平均*100
    for n in [10, 20, 60]:
        ma = data['close'].rolling(n).mean()
        data['bias_{}'.format(n)] = (data['close'] - ma) / ma * 100

    # 自适应均线
    # e = data['close'].diff(1).abs().rolling(60)
    return data


def down_trade_in(data):
    t = data
    # 这里不知道为什么日期筛选，放在外面会出错
    t = t[t['date'] > '2010-01-01']
    t = t[data['pct'] < -4]
    return t.index


def up_trade_in(data):
    t = data
    # t = t[t['date'] > '2010-01-01']
    # t = t[t['ma_10'] >= t['ma_60']][t['ma_10'].shift(1) < t['ma_60'].shift(1)]
    t = t[t['ma_60_slope'] >= 0]
    t = t[t['close'] >= t['ma_60']]
    t = t[t['ma_200_slope'] >= 0]
    t = t[abs(t['pct']) > 4]
    return t.index


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


# 以基础的止盈止损策略，判断能否盈利，不统计最终获利，但别的函数可以再次基础上再次计算，0失败，1成功，-1未知或无法买入，不计入
# 注意这里是按章当天收盘价买入来算的，用软件算涨跌幅的时候要从第二天开始算，即8/8买入，应该从8/9开始算，8/8当天涨跌不算
def trade_target(data, loss_pct, earning_pct):
    trade_target = []
    end_date = []
    for in_index in data.index:
        # 一字涨停无法买入
        if data['pct'].loc[in_index] > 9.9 and data['open'].loc[in_index] == data['close'].loc[in_index]:
            trade_target.append(-1)
            end_date.append(data['date'].loc[in_index])
            continue

        # 出入价位
        earning_stop_price = data['close'].loc[in_index] * (1 + earning_pct / 100)
        loss_stop_price = data['close'].loc[in_index] * (1 - loss_pct / 100)

        # 根据止损止盈价位，提取出第一个满足要求的缩影
        earning_index = data[(data['close'] > earning_stop_price) & (data.index > in_index)].index
        loss_index = data[(data['close'] < loss_stop_price) & (data.index > in_index)].index

        # 无法止损止盈
        if earning_index.empty and loss_index.empty:
            trade_target.append(-1)
            end_date.append(data['date'].loc[in_index])
        # 无法止盈
        elif earning_index.empty and not loss_index.empty:
            trade_target.append(0)
            end_date.append(data['date'].loc[loss_index[0]])
        # 无法止损
        elif not earning_index.empty and loss_index.empty:
            trade_target.append(1)
            end_date.append(data['date'].loc[earning_index[0]])
        # 止损止盈均可选择时间近的
        else:
            if earning_index[0] < loss_index[0]:
                trade_target.append(1)
                end_date.append(data['date'].loc[earning_index[0]])
            else:
                trade_target.append(0)
                end_date.append(data['date'].loc[loss_index[0]])

    data['trade_target'] = trade_target
    data['trade_target_end_date'] = end_date

    return data


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


# 主要用于和软件数据比较是否一致
def print_test(data):
    data[['date', 'ma_20', 'ma_60', 'ma_200']][300:320]
    data[['date', 'ma_20', 'bolling_upper', 'bolling_lower']][-240:-220]
    data[['date', 'dif', 'dea', 'macd']][-400:-380]
    # rsi的值有问题
    data[['date', 'rsi_12', 'rsi_24', 'rsi_48']][-300:-280]
    data[['date', 'k', 'd', 'j']][-500:-480]
    data[['date', 'bias_10', 'bias_20', 'bias_60']][-300:-280]
    data[['date', 'open', 'close', 'pct', 'trade_target', 'trade_target_end_date']][-40:]


if __name__ == '__main__':
    # 前复权，不然技术指标没有意义
    data = get_k_data('300725', 'd', 'qfq')
    k_day_data = data_retreatment(data)
    # t = virtual_trade_statics(data, up_trade_in, trade_out)
    k_day_data = trade_target(k_day_data, 10, 30)
