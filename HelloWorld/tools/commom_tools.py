import sys
from datetime import datetime
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates

sys.path.append("..")
from tools import share_statistic


def coefficient_correlation(compare_shares, st=None, ed=None, columns='pct_chg', names=[]):
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


def relative_growth(compare_shares, st=None, ed=None, columns='close', names=[]):
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
        t['cum_{}_{}'.format(columns, i)].map(share_statistic.kp2dig)

    cum = t[['cum_{}_{}'.format(columns, i) for i in range(len(compare_shares))] + ['date']]
    cum['date'] = cum['date'].apply(lambda date_str: datetime.strptime(date_str, '%Y-%m-%d').date())
    ax = cum.plot(x='date')
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%Y-%m-%d'))
    if names:
        ax.legend(names)
    return t

def generate_data(codes):
    data = []
    for code in codes:
        t = share_statistic.get_and_cache_k_date(code)
        data.append(t[0])
    return data
if __name__ == '__main__':
    codes = ['601186', '600510', 'sh', 'cyb']
    data = generate_data(codes)
    coefficient_correlation(data, st='2019-01-10', names=codes)
    relative_growth(data, st='2019-01-10', names=codes)
