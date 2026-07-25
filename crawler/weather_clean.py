import pandas as pd
from sqlalchemy import create_engine
import numpy as np
from weather_database import save_to_weather_db, get_weather_data
import datetime
from sqlalchemy import text

WEA_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_weather" 
}

all_station_code = ['C2F860', 'C2G870', 'C0G730', 'C0G940', 'C2K280', 'C0K390', 'C0K500', 
                    'V2K620', 'C0K590', 'C0K440', 'C0K550', 'A2K360', 'C0K480','C0M820', 
                    '72M700', 'C0I390', '42HA10', 'C0U720']

def clean():
    db_url = f"mysql+pymysql://{WEA_DB_CONFIG['user']}:{WEA_DB_CONFIG['password']}@{WEA_DB_CONFIG['host']}:{WEA_DB_CONFIG['port']}/{WEA_DB_CONFIG['database']}"
    engine = create_engine(db_url)

    clean_column = ['StnPres', 'StnPresMax', 'StnPresMin','Temperature', 'T Max', 'T Min', 
                    'RH', 'RHMin', 'WS', 'WD', 'WSGust', 'WDGust', 'Precp']


    sql = f'''SELECT * FROM `clean_weather` WHERE DATE(ObsTime) >= CURDATE() - INTERVAL 3 DAY'''
    df = pd.read_sql(sql, engine)
    if df.empty:
        return df
    
    # --- 0. 轉換ObsTime樣式，變成 xxxx-xx-xx ---
    df['ObsTime'] = pd.to_datetime(df['ObsTime']).dt.date

    df = df.sort_values(['Station_Code', 'ObsTime'])

    # --- 1. 處理缺失值 ---
    # groupby(Station_Code) 按照測站分類，並提取出
    # interpolate() 利用前一筆跟後一筆資料平均，填入缺失值
    df[clean_column] = df.groupby('Station_Code')[clean_column].transform(lambda x: x.interpolate())
    df[clean_column] = df.groupby('Station_Code')[clean_column].transform(lambda x: x.ffill())
    
    # --- 2. 處理重複值 ---
    repeat = df.duplicated().sum()
    if repeat != 0:
        df.drop_duplicates(inplace=True)

    # --- 3. 處理異常值 ---
    # print("資料異常值處理前")
    # print(df.describe().T) # 檢查資料分布

    df['RH'] = df['RH'].replace(0.0, np.nan)
    df['RHMin'] = df['RHMin'].replace(0.0, np.nan)
    # 前項遞補
    df['RH'] = df.groupby('Station_Code')['RH'].transform(lambda x: x.ffill())
    df['RHMin'] = df.groupby('Station_Code')['RHMin'].transform(lambda x: x.ffill())
    df.loc[(df['RHMin'] <= 10) & (df['RH'] >= 80), 'RHMin'] = df['RH'] * (df['Temperature'] / df['T Max'])

    # print("資料異常值處理後")
    # print(df.describe().T) # 檢查資料分布

    return df



if __name__ == '__main__':
    df = clean()
    # 只需要前一天的資料就好
    df = df[df['ObsTime'] == datetime.date.today() - datetime.timedelta(days=1)]
    if not df.empty:
        engine = get_weather_data()
        del_yesterday_sql = 'DELETE FROM `clean_weather` WHERE DATE(ObsTime) = CURDATE() - INTERVAL 1 DAY'
        with engine.connect() as conn:
            conn.execute(text(del_yesterday_sql))
            conn.commit()

        save_to_weather_db(df, 'clean_weather', 'append')
    
    
    
