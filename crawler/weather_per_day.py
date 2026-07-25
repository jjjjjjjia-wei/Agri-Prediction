import pandas as pd
import weather_database

def get_day_data():
    engine = weather_database.get_weather_data()

    # 找出昨天的24筆資料
    sql = f'''SELECT * FROM data_per_hour WHERE DATE(ObsTime) = CURDATE() - INTERVAL 1 DAY'''

    df = pd.read_sql(sql, engine)

    if df.empty:
        return
    
    obstime = pd.to_datetime(df["ObsTime"]).dt.date[0] # 取出第一個物件

    summary_df = df.groupby('Station_Code').agg({
        'StnPres': ['mean', 'max', 'min'],
        'Temperature': ['mean', 'max', 'min'],
        'RH': ['mean', 'min'],
        'WS': ['mean'],
        'WD': ['mean'],
        'WSGust': ['max'],
        'Precp': ['sum']
    })
    wdgust = df.groupby("Station_Code").apply(get_max_gust_dir)
    summary_df.columns = ['StnPres', 'StnPresMax', 'StnPresMin', 'Temperature', 'T Max', 'T Min',
                           'RH', 'RHMin', 'WS', 'WD', 'WSGust', 'Precp']
    summary_df['ObsTime'] = obstime
    summary_df['WDGust'] = wdgust

    # 把 Station_code 加回來
    summary_df = summary_df.reset_index() 

    # 更改欄位順序
    summary_df = summary_df[['ObsTime', 'Station_Code', 'StnPres', 'StnPresMax', 'StnPresMin', 'Temperature', 'T Max', 'T Min',
                           'RH', 'RHMin', 'WS', 'WD', 'WSGust', 'WDGust' ,'Precp']] 

    return summary_df

def get_max_gust_dir(group):
    if group['WSGust'].isna().all():
        return None
    else:
        # 找出最大陣風 (WSGust) 發生在第幾列
        max_index = group['WSGust'].idxmax()
    
    # 2. 透過定位 (loc)，回傳那一列的風向 (WDGust)
    return group.loc[max_index, 'WDGust']    

if __name__ == "__main__":
    df = get_day_data()
    if df is not None:
        weather_database.save_to_weather_db(df, 'original_weather', 'append') 
        weather_database.save_to_weather_db(df, 'clean_weather', 'append')