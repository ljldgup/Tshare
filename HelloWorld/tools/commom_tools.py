import sys
from datetime import datetime
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates

sys.path.append("..")
from tools import share_statistic


def coefficient_correlation(*compare_shares, basic_share, st=None, ed=None):
    t = basic_share.copy()
    t.rename(columns={'pct_chg': 'pct_0'}, inplace=True)
    # merge 去除重叠日期
    for i in range(len(compare_shares)):
        t = pd.merge(t[['pct_{}'.format(i) for i in range(i + 1)] + ['date']],
                     compare_shares[i][['date', 'pct_chg']], on='date')
        t.rename(columns={'pct_chg': 'pct_{}'.format(i + 1)}, inplace=True)

    for i in range(len(compare_shares)):
        t['{}-{}'.format(0, i + 1)] = t['pct_0'].rolling(30).corr(t['pct_{}'.format(i + 1)])

    t = t[['{}-{}'.format(0, i + 1) for i in range(len(compare_shares))] + ['date']]
    if st:
        t = t[t['date'] >= st]
    if ed:
        t = t[t['date'] <= ed]
    t['date'] = t['date'].apply(lambda date_str: datetime.strptime(date_str, '%Y-%m-%d').date())
    ax = t.plot(x='date')
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%Y-%m-%d'))


if __name__ == '__main__':
    data = []
    for code in ['002111', 'sh', 'sz', 'cyb']:
        t = share_statistic.get_and_cache_k_date(code)
        data.append(t[0])
    coefficient_correlation(data[1], data[2], data[3], basic_share=data[0])
