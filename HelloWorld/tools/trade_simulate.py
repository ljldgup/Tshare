import os

import pandas as pd


# 由于tushare的前复权数据有严重计算错误问题，这里考虑直接手动从东方财富后台拉数据
# 一般而言打开日k后，后台传输数据最大的就是日k，url一般是js?token=....
# 点开响应，等待片刻，复制其中data的数据，保存为[..]格式，文件名为股票代码

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
    data['ma_10'] = data['close'].rolling(10).mean()
    data['ma_20'] = data['close'].rolling(20).mean()
    data['ma_60'] = data['close'].rolling(60).mean()
    data['ma_200'] = data['close'].rolling(200).mean()
    # 斜率,除以收盘价保证他的相对性
    # 注意这里不能像前移，否则就是未来函数
    data['ma_20_slope'] = data['ma_20'].diff(1) / data['close']
    data['ma_60_slope'] = data['ma_60'].diff(1) / data['close']
    data['ma_200_slope'] = data['ma_200'].diff(1) / data['close']
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


if __name__ == '__main__':
    data = data_process('300033')
    data = data_retreatment(data)
    t = virtual_trade_statics(data, up_trade_in, trade_out)
