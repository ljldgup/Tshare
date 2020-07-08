from tools.share_statistic import get_and_cache_k_date, use_proxy
from sklearn.cluster import KMeans
import numpy as np


def share_period_genderate(data):
    pct_generate(data)
    i = 1
    ans = []
    date = []
    # t = data[['pct_chg', 'low_to_high', 'close_to_high', 'close_to_low', 'volume_pct']]
    t_data = data[['close', 'open', 'high', 'low']]
    while i + 20 < len(data):
        t = t_data.iloc[i:i + 20].values.reshape(1, -1)
        t = t - t.min()
        ans.append(t)
        date.append(data_d['date'].iloc[i])
        i += 10
    return np.concatenate(ans), date


def pct_generate(data):
    data['low_to_high'] = data['high'] - data['low']
    data['close_to_high'] = data['high'] - data['close']
    data['close_to_low'] = data['low'] - data['close']
    data['volume_pct'] = data['volume'].pct_change().fillna(0)


if __name__ == '__main__':
    use_proxy()

    data_d, data_w, data_m = get_and_cache_k_date('sh')
    x, date = share_period_genderate(data_d)
    kmeans = KMeans(n_clusters=8)
    y_pred = kmeans.fit_predict(x)
    rst = {}
    for label in set(y_pred):
        rst[label] = []

    for i, label in enumerate(y_pred):
        rst[label].append(date[i])
