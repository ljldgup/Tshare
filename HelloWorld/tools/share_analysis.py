# tools 报错把 外层Helloworld 文件夹 右键 make directory as -> source root
from tools.commom_tools import get_k_data
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import SGDClassifier, LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, scale, MinMaxScaler


from sklearn.svm import LinearSVC, SVC

from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
from datetime import datetime


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


# 生成技术指标
def technical_indicators_gen(data):
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
    for n in [20, 60, 200]:
        ma = data['close'].rolling(n).mean()
        data['bias_{}'.format(n)] = (data['close'] - ma) / ma * 100

    # 自适应均线
    # e = data['close'].diff(1).abs().rolling(60)
    return data


# 生成供训练用的参数
def train_feature_gen(data):
    # 均线波动范围交广，均线收盘价之间的百分比差
    data['ma_20_60_pct'] = (data['ma_20'] - data['ma_60']) / data['ma_60']
    data['ma_60_200_pct'] = (data['ma_60'] - data['ma_200']) / data['ma_200']
    data['ma_20_200_pct'] = (data['ma_20'] - data['ma_200']) / data['ma_200']

    # 短期涨幅累计
    data['pct_10'] = data['close'].pct_change(10)
    data['pct_20'] = data['close'].pct_change(20)
    data['pct_60'] = data['close'].pct_change(60)

    # 布林线相对
    data['close_bolling_upper'] = (data['close'] - data['bolling_upper']) / data['close']
    data['close_bolling_lower'] = (data['close'] - data['bolling_lower']) / data['close']

    # 成交量相对
    t = data['turnover'].rolling(20).mean()
    data['turnover_20_bias'] = (data['turnover'] - t) / t
    t = data['obv'].rolling(20).mean()
    data['obv_20_bias'] = (data['obv'] - t) / t


def period_data_generate(data):
    i = 1
    train_x = []
    train_y = []
    t_data = data[['close', 'open', 'high', 'low', 'turnover_rate']]
    while i + 21 < len(data):
        t = t_data.loc[i:i + 20].values.reshape(1, -1)
        train_x.append(data)
        train_y.append(data['trade_target'].loc[i + 21])
        i += 20
    return np.concatenate(train_x), np.concatenate(train_y)


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


def down_trade_in(data):
    t = data
    # 这里不知道为什么日期筛选，放在外面会出错
    t = t[t['date'] > '2010-01-01']
    t = t[data['pct'] < -4]
    return t.index





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


def coefficient_correlation(compare_shares, st=None, ed=None, columns='pct_chg', names=None):
    if names is None:
        names = []
    compare_shares = list(compare_shares)
    t = compare_shares[0][['date', columns]]
    if st:
        t = t[t['date'] >= st]
    if ed:
        t = t[t['date'] <= ed]

    # 这里转换会导致merge失败
    # t['date'] = t['date'].apply(lambda date_str: datetime.strptime(date_str, '%Y-%m-%d').date())
    t.rename(columns={columns: columns + '_0'}, inplace=True)
    for i in range(1, len(compare_shares)):
        compare_shares[i] = compare_shares[i][['date', columns]]
        compare_shares[i].rename(columns={columns: '{}_{}'.format(columns, i)}, inplace=True)
        t = pd.merge(t, compare_shares[i], on='date')

    for i in range(1, len(compare_shares)):
        t['{}-{}'.format(0, i)] = t[columns + '_0'].rolling(20).corr(t['{}_{}'.format(columns, i)])

    corr = t[['{}-{}'.format(0, i) for i in range(1, len(compare_shares))] + ['date']]
    corr['date'] = corr['date'].apply(lambda date_str: datetime.strptime(date_str, '%Y-%m-%d').date())
    ax = corr.plot(x='date')
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%Y-%m-%d'))

    if names:
        ax.legend(['{}-{}'.format(names[0], names[i]) for i in range(1, len(names))])
    return t


def relative_growth(compare_shares, st=None, ed=None, columns='close', names=None):
    if names is None:
        names = []
    compare_shares = list(compare_shares)
    t = compare_shares[0][['date', columns]]
    if st:
        t = t[t['date'] >= st]
    if ed:
        t = t[t['date'] <= ed]

    # 这个会导致merge失败
    # t['date'] = t['date'].apply(lambda date_str: datetime.strptime(date_str, '%Y-%m-%d').date())
    t.rename(columns={columns: columns + '_0'}, inplace=True)
    for i in range(1, len(compare_shares)):
        compare_shares[i] = compare_shares[i][['date', columns]]
        compare_shares[i].rename(columns={columns: '{}_{}'.format(columns, i)}, inplace=True)
        t = pd.merge(t, compare_shares[i], on='date')

    for i in range(len(compare_shares)):
        t['cum_{}_{}'.format(columns, i)] = t['close_' + str(i)] / t['close_' + str(i)][t.index[0]] - 1
        t['cum_{}_{}'.format(columns, i)].map(two_digit_percent)

    cum = t[['cum_{}_{}'.format(columns, i) for i in range(len(compare_shares))] + ['date']]
    cum['date'] = cum['date'].apply(lambda date_str: datetime.strptime(date_str, '%Y-%m-%d').date())
    ax = cum.plot(x='date')
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%Y-%m-%d'))
    if names:
        ax.legend(names)
    return t


def share_period_genderate(data):
    i = 1
    ans = []
    date = []
    t_data = data[['close', 'open', 'high', 'low']]
    while i + 20 < len(data):
        t = t_data.iloc[i:i + 20].values.reshape(1, -1)
        t = t - t.min()
        ans.append(t)
        date.append('{}~{}'.format(data_d['date'].iloc[i], data_d['date'].iloc[i + 20]))
        i += 20
    return np.concatenate(ans), date


def cluster_test(data):
    x, date = share_period_genderate(data)
    kmeans = KMeans(n_clusters=12)
    y_pred = kmeans.fit_predict(x)

    '''
    # dbscan 效果很差,很多为1的簇，min_samples大了就是离群点
    # 测试了一下，eps 1000比较合适,min_samples 1比较合适
    for interval in range(100, 10000, 100):
        dbscan = DBSCAN(eps=interval, min_samples=1)
        y_pred = dbscan.fit_predict(x)
        print(interval, set(y_pred))

    for min_samples_num in range(1, 10):
        dbscan = DBSCAN(eps=100, min_samples=min_samples_num)
        y_pred = dbscan.fit_predict(x)
        print(min_samples_num, set(y_pred))
    dbscan = DBSCAN(eps=1000, min_samples=1)
    y_pred = dbscan.fit_predict(x)
    '''

    rst = {}
    for label in set(y_pred):
        rst[label] = []

    for i, label in enumerate(y_pred):
        rst[label].append(date[i])
    return rst


if __name__ == '__main__':
    '''
    codes = ['601186', '600510', 'sh', 'cyb']
    data_d, data_w, data_m = get_k_data('sh')
    cluster_test(data_d)
    coefficient_correlation(data_d, st='2019-01-10', names=codes)
    relative_growth(data_d, st='2019-01-10', names=codes)
    '''
    data = get_k_data('000725', 'd', 'qfq')
    data = technical_indicators_gen(data)
    train_feature_gen(data)
    # t = virtual_trade_statics(data, up_trade_in, trade_out)
    trade_target(data, 10, 30)
    data = data.dropna()
    data = data[data['trade_target'] != -1]
    feature_list = ['pct_10', 'pct_20', 'pct_60']

    X = data[feature_list].values
    y = data['trade_target'].values

    # 标准化
    # scaler = StandardScaler()
    # x_scaled = scaler.fit_transform(X)

    # 归一化
    scaler = MinMaxScaler()
    x_scaled = scaler.fit_transform(X)

    '''
    X, y = make_classification(
        n_samples=1000, n_features=15, n_classes=2,
        n_redundant=4, n_informative=10,
        random_state=22, n_clusters_per_class=1,
        scale=100)
    '''
    train_x, test_x, train_y, test_y = train_test_split(x_scaled, y, train_size=0.7)
    # RandomForestClassifier 和 KNeighborsClassifier有正常结果，其他预测值都是0
    # classifier = LinearSVC(C=1, loss="hinge")
    # classifier = SVC(kernel="rbf", C=0.01)
    # classifier = KNeighborsClassifier(n_neighbors=5)
    # classifier = SGDClassifier(random_state=42)
    # classifier = RandomForestClassifier(random_state=42)
    classifier = GradientBoostingClassifier()
    # classifier = LogisticRegression()
    '''
    '''
    classifiers = [LinearSVC(C=1), SVC(kernel="rbf", C=0.01), KNeighborsClassifier(n_neighbors=5),
                       SGDClassifier(random_state=42), RandomForestClassifier(random_state=42),
                       GradientBoostingClassifier(), LogisticRegression()]
    for classifier in classifiers:
        classifier.fit(train_x, train_y)
        pred_y = classifier.predict(test_x)
        print('-------------------------------------')
        print(classifier)
        print('accuracy_score', accuracy_score(pred_y, test_y))
        print('precision_score', precision_score(pred_y, test_y))
        print('recall_score', recall_score(pred_y, test_y))
        print('f1_score', f1_score(pred_y, test_y))
