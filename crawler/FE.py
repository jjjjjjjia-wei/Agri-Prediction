from weather_database import get_weather_data, save_to_weather_db
from trans_database import get_trans_data
import pandas as pd
from sqlalchemy import create_engine
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def transform_obstime():
    # 先把天氣資料按照"一天多個測站"分類
    # 從資料庫提取天氣資料
    db_engine = get_weather_data()
    sql = 'SELECT * FROM `2020-2025_clean_weather`'
    df = pd.read_sql(sql, db_engine)

    # 轉換表格
    clean_column = ['StnPres', 'StnPresMax', 'StnPresMin','Temperature', 'T Max', 'T Min', 
                        'RH', 'RHMin', 'WS', 'WD', 'WSGust', 'WDGust', 'Precp']
    df_wide = df.pivot_table(index='ObsTime', columns='Station_Code', values=clean_column)
    df_wide.columns = [f"{col[1]}_{col[0]}" for col in df_wide.columns]
    df_wide = df_wide.reset_index()

    # 存回資料庫
    save_to_weather_db(df_wide, "2020-2025_all_stations_daily")
    
    return df_wide

def trans_data():
    sql = 'SELECT * FROM la1_clean WHERE TransDate<="2025-12-31"'
    engine =  get_trans_data()
    trans_df = pd.read_sql(sql, engine)

    return trans_df

# --- 開始特徵工程 ---
def weather_FE():
    weather_df = transform_obstime()
    weather_df['ObsTime'] = pd.to_datetime(weather_df['ObsTime'])
    weather_df = weather_df.sort_values('ObsTime')
    new_features = {}
    
    # 測站代號
    all_station_code = ['C2F860', 'C0G870', 'C0G730', 'C0G750', 'C0K280', 'C0K390', 'C0K500', 
                    'V2K620', 'C0K520', 'C0K440', 'C0K550', 'A2K360', 'C0K480']
    
    # --- 1. 滾動平均 ---
    for station in all_station_code:
        # 7 天、14天的 累積降雨量 and 平均降雨量
        new_features[f'{station}_7days_sum_Precp'] = weather_df[f'{station}_Precp'].rolling(window=7).sum()
        new_features[f'{station}_14days_sum_Precp'] = weather_df[f'{station}_Precp'].rolling(window=14).sum()
        new_features[f'{station}_7days_means_Precp'] = weather_df[f'{station}_Precp'].rolling(window=7).mean()
        new_features[f'{station}_14days_means_Precp'] = weather_df[f'{station}_Precp'].rolling(window=14).mean()
        # 7 天、14天、21天、30天、45天、60天、75天、90天的氣溫平均
        new_features[f'{station}_7days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=7).mean()
        new_features[f'{station}_14days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=14).mean()
        new_features[f'{station}_21days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=21).mean()
        new_features[f'{station}_30days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=30).mean()
        new_features[f'{station}_45days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=45).mean()
        new_features[f'{station}_60days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=60).mean()
        new_features[f'{station}_75days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=75).mean()
        new_features[f'{station}_90days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=90).mean()
        # 7 天、14天、21天、30天的相對溼度平均
        new_features[f'{station}_7days_mean_RH'] = weather_df[f"{station}_RH"].rolling(window=7).mean()
        new_features[f'{station}_14days_mean_RH'] = weather_df[f"{station}_RH"].rolling(window=14).mean()
        new_features[f'{station}_21days_mean_RH'] = weather_df[f"{station}_RH"].rolling(window=21).mean()
        new_features[f'{station}_30days_mean_RH'] = weather_df[f"{station}_RH"].rolling(window=30).mean()

        # 過去 14 天內，累積降雨量超過 50mm 的天數
        is_heavy_rain = (weather_df[f'{station}_Precp'] >= 50).astype(int)
        new_features[f'{station}_heavy_rain_in_7days'] = is_heavy_rain.rolling(window=7).sum()

        # 過去 7 天內，氣溫超過 30 度的日子有幾天
        is_over_30deg = (weather_df[f'{station}_Temperature'] > 30).astype(int)
        new_features[f'{station}_over_30deg'] = is_over_30deg.rolling(window=7).sum()

        # 過去 7 天內，氣溫低於 15 度的日子有幾天
        is_less_15deg = (weather_df[f'{station}_Temperature'] < 15).astype(int)
        new_features[f'{station}_less_15deg'] = is_less_15deg.rolling(window=7).sum()

    
    # 四季 0:春 1:夏 2:秋 3:冬
    season_dict = {1:3, 2:3, 3:0, 4:0, 5:0, 6:1, 7:1, 8:1, 9:2, 10:2, 11:2, 12:3}
    new_features['season'] = weather_df['ObsTime'].dt.month.map(season_dict)

    # 是否為颱風季 7~9月為颱風季 10~11月也會有秋颱
    typhoon_season = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:2, 8:2, 9:2, 10:1, 11:1, 12:0}
    new_features['typhoon'] = weather_df['ObsTime'].dt.month.map(typhoon_season)

    # 星期幾
    new_features['day_of_week'] = weather_df['ObsTime'].dt.dayofweek

    # 是否為梅雨季
    rainy_season = {1:0, 2:0, 3:0, 4:0, 5:1, 6:1, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0}
    new_features['rainy_season'] = weather_df['ObsTime'].dt.month.map(rainy_season)

    new_features_df = pd.DataFrame(new_features)
    weather_df = pd.concat([weather_df, new_features_df], axis=1) # 橫向合併
    return weather_df

def trans_FE():
    trans_df = trans_data()
    trans_df['TransDate'] = pd.to_datetime(trans_df['TransDate'])
    trans_df = trans_df.sort_values('TransDate')

    # 昨天以及前天的平均價
    trans_df['yesterday_avgP'] = trans_df.groupby("MarketCode")['Avg_Price'].shift(1)
    trans_df['two_day_ago_avgP'] = trans_df.groupby("MarketCode")['Avg_Price'].shift(2)
    # 平均價趨勢
    trans_df['yesterday_fluctuation'] = trans_df['yesterday_avgP'] - trans_df['two_day_ago_avgP']

    # 昨天同一個市場的交易量
    trans_df['yesterday_transQ'] = trans_df.groupby('MarketCode')['Trans_Quantity'].shift(1)

    # 過去 7 天平均交易量
    trans_df['transQ_avg_7day'] = trans_df.groupby('MarketCode')['Trans_Quantity'].transform(lambda x: x.rolling(window=7).mean())

    return trans_df

def merge_weather_trans(trans_df, weather_df):
    # 合併成一個大表
    merged_df = pd.merge(trans_df, weather_df, left_on='TransDate', right_on='ObsTime', how='left')
    
    # 清除因滾動平均留下來的空值
    merged_df = merged_df.dropna()

    return merged_df

def save_to_merge_db(merged_df, table):
    
    DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_merge"
    }
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    db_engine = create_engine(db_url)

    try:
        merged_df.to_sql(
            name = table,
            con = db_engine,
            if_exists = 'replace',
            index = False
        )
        logging.info('特徵工程資料寫入成功')

    except Exception as e:
        logging.error(f'特徵工程資料寫入失敗: {e}')

    

    
if __name__ == "__main__":
    trans_df = trans_FE()
    weather_df = weather_FE()
    data_2020_2025 = merge_weather_trans(trans_df, weather_df)
    save_to_merge_db(merged_df=data_2020_2025, table='merged_fe')


