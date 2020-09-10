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
        ans['pct_chg'] = ans['close'].pct_change().fillna(0) * 100

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
    data['obv'] = (data['pct_chg'].map(lambda x: 1 if x > 0 else -1) * data['volume']).cumsum()

    # wr （Hn—C）÷（Hn—Ln）×100 其中：C为计算日的收盘价，Ln为N周期内的最低价，Hn为N周期内的最高价，
    data['wr'] = (data['high'].rolling(10).max() - data['close']) / (
            data['high'].rolling(10).max() - data['high'].rolling(10).min())
    data['wr'] = (data['high'].rolling(20).max() - data['close']) / (
            data['high'].rolling(20).max() - data['high'].rolling(20).min())

    #  RSV指标主要用来分析市场是处于“超买”还是“超卖”：RSV高于80%时候市场即为超买；RSV低于20%时候，市场为超卖
    #  rsv =(收盘价 – n日内最低价)/(n日内最高价 – n日内最低价)×100
    t_min = data['low'].rolling(24).min()
    t_max = data['high'].rolling(24).max()
    data['rsv_24'] = (data['close'] - t_min) / (t_max - t_min) * 100
    # 当日K值=2/3×前一日K值+1/3×当日RSV
    #  α=1/(1+com)
    data['k'] = data['rsv_24'].ewm(com=2, adjust=False).mean()
    # 当日D值 = 2 / 3×前一日D值 + 1 / 3×当日K值
    data['d'] = data['k'].ewm(com=2).mean()
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
    MA = data['close'].rolling(20).mean()
    MD = data['close'].rolling(20).std()  # ddof代表标准差自由度
    # 计算上轨、下轨道
    data['bolling_upper'] = MA + 2 * MD
    data['bolling_lower'] = MA - 2 * MD

    # 乖离率
    # BIAS=(收盘价-收盘价的N日简单平均)/收盘价的N日简单平均*100
    for n in [10, 20, 60]:
        ma = data['close'].rolling(n).mean()
        data['bias_{}'.format(n)] = (data['close'] - ma) / ma * 100

    return data


def down_trade_in(data):
    t = data
    # 这里不知道为什么日期筛选，放在外面会出错
    t = t[t['date'] > '2010-01-01']
    t = t[data['pct_chg'] < -4]
    return t.index


def up_trade_in(data):
    t = data
    # t = t[t['date'] > '2010-01-01']
    # t = t[t['ma_10'] >= t['ma_60']][t['ma_10'].shift(1) < t['ma_60'].shift(1)]
    t = t[t['ma_60_slope'] >= 0]
    t = t[t['close'] >= t['ma_60']]
    t = t[t['ma_200_slope'] >= 0]
    t = t[abs(t['pct_chg']) > 4]
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
    data[['date', 'ma_20', 'ma_60', 'ma_200']].tail()
    data[['date', 'ma_20', 'bolling_upper', 'bolling_lower']][-240:-220]
    data[['date', 'dif', 'dea', 'macd']][-200:-180]
    data[['date', 'rsi_12', 'rsi_24', 'rsi_48']][-300:-280]
    data[['date', 'k', 'd', 'j']][-300:-280]
    data[['date', 'bias_20', 'bias_60', 'bias_200']][-300:-280]


if __name__ == '__main__':
    # 前复权，不然技术指标没有意义
    data = get_k_data('300725', 'qfq')
    k_day_data = data_retreatment(data[0])
    # t = virtual_trade_statics(data, up_trade_in, trade_out)
