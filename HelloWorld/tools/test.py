import datetime


class Stock:
    def __init__(self, stock_code):
        self.stock_code = stock_code
        now_date = datetime.datetime.now()
        if now_date.hour > 15:
            begin_date = now_date - datetime.timedelta(days=30)
            end_date = now_date
        else:
            begin_date = now_date - datetime.timedelta(days=30)
            end_date = now_date - datetime.timedelta(days=1)

        begin_date_str = begin_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        stock_data = ts.get_hist_data(stock_code, start=begin_date_str, end=end_date_str)

        self.stock_data = stock_data.sort_index(0)

    def save_data(self):
        self.stock_data.to_pickle("stock_data_{}.pickle".format(self.stock_code))

    @staticmethod
    def get_smoothed_moving_avg(df, column, window):
        column_name = '{}_{}_smma'.format(column, window)
        smma = df[column].ewm(
            ignore_na=False, alpha=1.0 / window,
            min_periods=0, adjust=True).mean()
        df[column_name] = smma

    def get_rsi(self, n_days):
        """ 计算N天的RSI指标
        计算方式参照链接: https://en.wikipedia.org/wiki/Relative_strength_index
        更易于理解的介绍参照 https://wiki.mbalib.com/wiki/RSI

        该指标较为困难，计算结果可以在东方财富等网站进行数值比较。不同计算方式可能存在一定误差
        :param df: data
        :param n_days: N days
        :return: None
        """
        df = self.stock_data
        n_days = int(n_days)
        d = df['close'] - df['close'].shift(1)

        df['closepm'] = (d + d.abs()) / 2
        df['closenm'] = (-d + d.abs()) / 2
        closepm_smma_column = 'closepm_{}_smma'.format(n_days)
        closenm_smma_column = 'closenm_{}_smma'.format(n_days)
        self.get_smoothed_moving_avg(df, 'closepm', n_days)
        self.get_smoothed_moving_avg(df, 'closenm', n_days)

        p_ema = df[closepm_smma_column]
        n_ema = df[closenm_smma_column]

        rs_column_name = 'rs_{}'.format(n_days)
        rsi_column_name = 'rsi_{}'.format(n_days)
        df[rs_column_name] = rs = p_ema / n_ema
        df[rsi_column_name] = 100 - 100 / (1.0 + rs)

        columns_to_remove = ['closepm',
                             'closenm',
                             closepm_smma_column,
                             closenm_smma_column]

        self.stock_data = df.drop(columns_to_remove, axis=1)

    def get_rsv(self, n_days):
        """ 计算N天的RSV (Raw Stochastic Value)
        参照链接: 该值作为KDJ指标的计算前提
        https://wiki.mbalib.com/wiki/%E9%9A%8F%E6%9C%BA%E6%8C%87%E6%A0%87

        该作为KDJ指标的中间参数较简单，适合学生水平较薄弱时去做
        :param df: data
        :param n_days: N days
        :return: None
        """
        df = self.stock_data
        n_days = int(n_days)
        column_name = 'rsv_{}'.format(n_days)
        low_min = df['low'].rolling(
            min_periods=1, window=n_days, center=False).min()
        high_max = df['high'].rolling(
            min_periods=1, window=n_days, center=False).max()

        cv = (df['close'] - low_min) / (high_max - low_min)
        df[column_name] = cv.fillna(0).astype('float64') * 100

# 平安银行
stock_000001 = Stock("000001")
stock_000001.get_rsi(6)
stock_000001.get_rsv(6)
print(stock_000001.stock_data['rsi_6'])
print(stock_000001.stock_data['rsv_6'])

# 数据库操作部分省略，可采用pyodbc、pymysql等等工具连接
# 导出报表操作省略，如果以上步骤难度大，则此处仅要求输出CSV
