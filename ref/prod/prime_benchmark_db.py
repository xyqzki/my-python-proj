
import mysql.connector
import pandas as pd
from sqlalchemy import create_engine

conn = mysql.connector.connect(user='min', password='123456', host='10.9.19.232', database='benchmark')

engine = create_engine("mysql+mysqldb://min:123456@10.9.19.232/benchmark")

benchmark_info_dict = {
        
        'AssetClass': ['Equity', 'Equity' ], 
        'SubAssetClass': ['Emerging Markets', 'Developed Markets'],
        'BenchmarkName': ['MSCI Emerging Markets Gross Return USD Index', 'MSCI World Net TR USD Index'],
        'Ticker': ['M2EF Index', 'NDDUWI Index']
        
        }


benchmark_info_df = pd.DataFrame(benchmark_info_dict)

benchmark_info_df.to_sql('benchmarkinfo', con=engine, if_exists='append', index=False)

#benchmark_info_df.to_sql('benchmarkinfo', conn, if_exists='append', index=False)


