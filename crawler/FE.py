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
    sql = 'SELECT * FROM `clean_weather` WHERE DATE(ObsTime) >= CURDATE() - INTERVAL 150 DAY'
    df = pd.read_sql(sql, db_engine)
    df_len = len(df)
    print(f"天氣資料表的資料長度:{df_len}")
    if df_len == 0:
        logging.error(f'天氣資料表沒有提取出資料')
        return 

    # 轉換表格
    clean_column = ['Temperature', 'RH', 'Precp']
    df_wide = df.pivot_table(index='ObsTime', columns='Station_Code', values=clean_column)
    df_wide.columns = [f"{col[1]}_{col[0]}" for col in df_wide.columns]
    df_wide = df_wide.reset_index()
    df_wide_newest = df_wide.tail(1)

    # 存回資料庫
    save_to_weather_db(df_wide_newest, "all_stations_daily", 'append')
    return df_wide

def trans_data():
    sql = 'SELECT * FROM la1_clean WHERE DATE(TransDate) >= CURDATE() - INTERVAL 150 DAY'
    engine =  get_trans_data()
    trans_df = pd.read_sql(sql, engine)
    df_len = len(trans_df)
    print(f"交易資料表的資料長度:{df_len}")
    if df_len == 0:
        logging.error(f'天氣資料表沒有提取出資料')

    return trans_df

# --- 開始特徵工程 ---
def weather_FE():
    weather_df = transform_obstime()
    weather_df['ObsTime'] = pd.to_datetime(weather_df['ObsTime'])
    weather_df = weather_df.sort_values('ObsTime')
    new_features = {}
    
    # 測站代號
    all_station_code = ['C2F860', 'C2G870', 'C0G730', 'C0G940', 'C2K280', 'C0K390', 'C0K500', 
                    'V2K620', 'C0K590', 'C0K440', 'C0K550', 'A2K360', 'C0K480','C0M820', 
                    '72M700', 'C0I390', '42HA10', 'C0U720']
    
    # --- 1. 滾動平均 ---
    for station in all_station_code:
        # 7 天的 累積降雨量
        new_features[f'{station}_7days_sum_Precp'] = weather_df[f'{station}_Precp'].rolling(window=7).sum()
        
        # 7 天、14天的氣溫平均
        new_features[f'{station}_7days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=7).mean()
        new_features[f'{station}_14days_mean_tem'] = weather_df[f'{station}_Temperature'].rolling(window=14).mean()
        
        # 抓高溫高濕的病害高風險天數 (Temp > 25 且 RH > 80)
        is_rot_risk = ((weather_df[f'{station}_Temperature'] > 25) & (weather_df[f'{station}_RH'] > 80)).astype(int)
        new_features[f'{station}_rot_risk_7d'] = is_rot_risk.rolling(window=7, min_periods=1).sum()

        # 過去 14 天內，累積降雨量超過 30mm 的天數
        is_heavy_rain = (weather_df[f'{station}_Precp'] >= 30).astype(int)
        new_features[f'{station}_heavy_rain_in_7days'] = is_heavy_rain.rolling(window=7).sum()
        # 生長期幼苗災害特徵 (抓 60 天前育苗期是否遭遇暴雨摧毀，保留 75~90 天生長週期邏輯)
        new_features[f'{station}_heavy_rain_lag60'] = is_heavy_rain.shift(60).fillna(0)

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

    # 從昨天開始往前推 7 天的平均交易量
    trans_df['transQ_avg_7day'] = trans_df.groupby('MarketCode')['Trans_Quantity'].transform(lambda x: x.shift(1).rolling(window=7).mean())

    # 昨天的最高價
    trans_df['yesterday_upperP'] = trans_df.groupby('MarketCode')['Upper_Price'].shift(1)

    # 昨天的中價
    trans_df['yesterday_middleP'] = trans_df.groupby('MarketCode')['Middle_Price'].shift(1)
    
    # 昨天的最低價
    trans_df['yesterday_lowerP'] = trans_df.groupby('MarketCode')['Lower_Price'].shift(1)

    # 刪除 '當日'最高價、中價、最低價、交易量，以防止當日洩漏
    trans_df = trans_df.drop(columns=['Upper_Price', 'Middle_Price', 'Lower_Price', 'Trans_Quantity'])

    return trans_df

def merge_weather_trans(trans_df, weather_df):
    trans_df = trans_df.sort_values('TransDate')
    weather_df = weather_df.sort_values('ObsTime')
    
    # 合併成一個大表
    merged_df = pd.merge(trans_df, weather_df, left_on='TransDate', right_on='ObsTime', how='left')
    
    # 清除流水號ID與多餘的ObsTime
    merged_df = merged_df.drop(columns=['ID', 'ObsTime'], errors='ignore')
    merged_df = merged_df.ffill()
    merged_df = merged_df.dropna()
    
    return merged_df

def save_to_merge_db(merged_df, table, if_exist):
    
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
            if_exists = if_exist, 
            index = False
        )
        logging.info('特徵工程資料寫入成功')

    except Exception as e:
        logging.error(f'特徵工程資料寫入失敗: {e}')

    

    
if __name__ == "__main__":
    trans_df = trans_FE()
    weather_df = weather_FE()
    merge_df = merge_weather_trans(trans_df, weather_df)
    latest_date = merge_df['TransDate'].max()
    print(f"最新日期為: {latest_date}")
    newest_data = merge_df[merge_df['TransDate']==latest_date]
    save_to_merge_db(newest_data, table='merged_fe', if_exist='append')

    
