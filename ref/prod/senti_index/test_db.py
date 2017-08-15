import pandas as pd
from db import NewsDatabase


news_db = NewsDatabase()

df = pd.read_sql("SELECT * FROM newsdb.t_hk_stock_news where symbol='hk00700' and is_repeat=0", news_db.engine)
print(df['title'].tail(5))

df = pd.read_sql("SELECT * FROM newsdb.t_hk_stock_news where symbol='hk00001' and is_repeat=0", news_db.engine)
print(df['title'].tail(5))

news_db.tunnel.stop()