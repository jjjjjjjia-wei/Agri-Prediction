import pandas as pd
from glob import glob
import os

def resrt_obstime():
    all_frames = [] # 儲存修改完的資料
    citys = os.listdir('../weather_csvdata')
    for city in citys:
        countrys = os.listdir(f'../weather_csvdata/{city}')
        if os.path.isfile(f'../weather_csvdata/{city}/{countrys[0]}'): # 這個城市只有一個測站
            monthly_data = countrys[:]
            station_code = monthly_data[0].split('-')[0]
            # 取出年度以及月份
            for data in monthly_data:
                part = data.split('-')
                year = part[1]
                month = part[2].replace('.csv', '')
                # 修改 ObsTime
                data = pd.read_csv(f'../weather_csvdata/{city}/{data}', header=1)
                new_obstime = year + '-' + month + '-' + data['ObsTime'].astype(str)
                data['ObsTime'] = new_obstime
                data['Station_Code'] = station_code
                all_frames.append(data)

        else: # 這個城市有多個測站
            for country in countrys:
                monthly_data = os.listdir(f'../weather_csvdata/{city}/{country}')
                station_code = monthly_data[0].split('-')[0]
                # 取出年度以及月份
                for data in monthly_data:
                    part = data.split('-')
                    year = part[1]
                    month = part[2].replace('.csv', '')
                    # 修改 ObsTime
                    data = pd.read_csv(f'../weather_csvdata/{city}/{country}/{data}', header=1)
                    new_obstime = year + '-' + month + '-' + data['ObsTime'].astype(str)
                    data['ObsTime'] = new_obstime
                    data['Station_Code'] = station_code
                    all_frames.append(data)
    return all_frames

def merge():
    df_list = resrt_obstime()
    origin_weather_df = pd.concat(df_list, axis=0, ignore_index=True)
    return origin_weather_df

# 資料清洗
def data_clean(weather_df): 
    # ObsTime 改成 Datetime Object
    weather_df['ObsTime'] = pd.to_datetime(weather_df['ObsTime'])
    
    ctnum = ['StnPres', 'StnPresMax', 'StnPresMin', 'Temperature', 'T Max', 'T Min',
             'RH', 'RHMin', 'WS', 'WD', 'WSGust', 'WDGust', 'Precp', 'GloblRad', 'SeaPres', 
            'Td dew point', 'PrecpHour', 'PrecpMax10', 'SunShine', 'SunshineRate', 'Cloud Amount Sat', 
            'TxSoil0cm', 'TxSoil5cm', 'TxSoil10cm', 'TxSoil20cm', 'TxSoil30cm', 'TxSoil50cm', 'TxSoil100cm',
            'PrecpMax60']
    
    weather_df = weather_df.replace({'--':'NaN', '/':'Nan', 'T':0.1})

    for column in ctnum: 
        weather_df[f'{column}'] = pd.to_numeric(weather_df[f'{column}'], errors='coerce')

    move_station_code = weather_df.pop("Station_Code") # 抽出
    weather_df.insert(1, 'Station_Code', move_station_code) # 放到第二欄
    
    return weather_df

def plot(weather_df):
    import matplotlib
    import matplotlib.pyplot as plt
    # station_code = ['C0G730', 'C0G870', 'C0G750', '72M700', 'C0D360', 'C0I480', 'U2HA40', 'C2F860', 'C0O900',
    #                 'C0S600', 'C0U720', 'C0K520', 'C0K440', 'C0K480', 'V2K620', 'C0K550', 'C0K280', 'A2K360', 
    #                 'C0K390', 'C0K500']
    # for station in station_code:
    

# if __name__ == '__main__':
#     weather_df = data_clean(merge())
#     weather_df.head(10)
#     weather_df.shape
#     weather_df.info()