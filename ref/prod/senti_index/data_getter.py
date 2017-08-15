import pandas as pd
from db import NewsDatabase
from functools import lru_cache

news_db = NewsDatabase()

#@lru_cache()
def adj_ohlcv(symbols):
    df = pd.read_sql(
        "SELECT symbol, tradingDay as date, openPrice as open, closePrice as close, highPrice as high, "
        "lowPrice as low, turnoverVolume as volume "
        "FROM klinedb.t_hk_stock_day_kline_forward "
        "WHERE symbol IN %(symbols)s",
        news_db.engine,
        params={'symbols': [s.lower() for s in symbols]},
        parse_dates={'date': {'format': '%Y%m%d'}}
    )
    rv = {}
    for sym, sub_df in df.groupby('symbol'):
        idx = pd.bdate_range(sub_df['date'].min(), sub_df['date'].max())
        this = sub_df.set_index('date')
        this.drop('symbol', axis=1, inplace=True)
        this = this.reindex(idx, method='ffill')
        rv[sym.upper()] = this
    return pd.Panel(rv)