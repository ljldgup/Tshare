# tools 报错把 外层Helloworld 文件夹 右键 make directory as -> source root
from tools.commom_tools import two_digit_percent, get_k_data

from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
from datetime import datetime


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
    codes = ['601186', '600510', 'sh', 'cyb']

    data_d, data_w, data_m = get_k_data('sh')
    cluster_test(data_d)
    # use_proxy()
    # coefficient_correlation(data_d, st='2019-01-10', names=codes)
    # relative_growth(data_d, st='2019-01-10', names=codes)
