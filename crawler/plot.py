import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

AGRI_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_transcation"
}

WEA_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_weather" 
}
all_market_code = ['104','109','220','241','260','338','400','420','512',
                   '514','540','648','800','830','900','930','950']
all_station_code = ['C2F860', 'C0G870', 'C0G730', 'C0G750', 'C0K280', 'C0K390', 'C0K500', 
                    'V2K620', 'C0K520', 'C0K440', 'C0K550', 'A2K360', 'C0K480']

def get_trans_data_from_db(market_code):
    # 建立引擎
    db_url = f"mysql+pymysql://{AGRI_DB_CONFIG['user']}:{AGRI_DB_CONFIG['password']}@{AGRI_DB_CONFIG['host']}:{AGRI_DB_CONFIG['port']}/{AGRI_DB_CONFIG['database']}"
    engine = create_engine(db_url)
  
    # 提取市場的資料
    sql = f"""
    SELECT TransDate, Avg_Price, Upper_Price, Lower_Price
    FROM la1
    WHERE MarketCode = '{market_code}'
    ORDER BY TransDate;
    """

    # pd.read_sql() 回傳值直接是DataFrame
    df = pd.read_sql(sql, engine)
    df['TransDate'] = pd.to_datetime(df["TransDate"])
    
    return df

def trans_plot():
    # for market_code in all_market_code:
    #     df = get_trans_data_from_db(market_code)
    #     plt.plot(df['TransDate'], df['Upper_Price'], label = 'Upper')
    #     plt.plot(df['TransDate'], df['Avg_Price'], label = 'Avg')
    #     plt.plot(df['TransDate'], df['Lower_Price'], label = 'Lower')
    #     plt.title(f'Price at {market_code} market')
    #     plt.legend()
    #     plt.show()
    market_code = '540' 
    df = get_trans_data_from_db(market_code)
    plt.plot(df['TransDate'], df['Upper_Price'], label = 'Upper')
    plt.plot(df['TransDate'], df['Avg_Price'], label = 'Avg')
    plt.plot(df['TransDate'], df['Lower_Price'], label = 'Lower')
    plt.title(f'Price at {market_code} market')
    plt.legend()
    plt.show()


check_column = 'Temperature'
def get_wea_data_from_db(station_code):
    db_url = f"mysql+pymysql://{WEA_DB_CONFIG['user']}:{WEA_DB_CONFIG['password']}@{WEA_DB_CONFIG['host']}:{WEA_DB_CONFIG['port']}/{WEA_DB_CONFIG['database']}"
    engine = create_engine(db_url)

    # 提取天氣資料
    sql = f"""
    SELECT ObsTime, {check_column} 
    FROM `2020-2025_weather`
    WHERE Station_Code = '{station_code}'
    ORDER BY ObsTime;
    """

    df = pd.read_sql(sql, engine)
    df['ObsTime'] = pd.to_datetime(df["ObsTime"])

    return df

def weather_plot():
    for station_code in all_station_code:
        df = get_wea_data_from_db(station_code)
        plt.plot(df['ObsTime'], df[check_column], label = check_column)
        plt.title(f' at {station_code} ')
        plt.legend()
        plt.show()

if __name__ == "__main__":
    # print(trans_df.head())
    # trans_df.info()
    # trans_plot()
    weather_plot()