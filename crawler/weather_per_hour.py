import requests
import logging
from weather_database import save_to_weather_db
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

all_station_code = ['C2F860', 'C2G870', 'C0G730', 'C0G940', 'C2K280', 'C0K390', 'C0K500', 
                    'V2K620', 'C0K590', 'C0K440', 'C0K550', 'A2K360', 'C0K480','C0M820', 
                    '72M700', 'C0I390', '42HA10', 'C0U720']
station_str = ','.join(all_station_code)

def get_data_per_hour():
    logging.info("開始呼叫氣象API...")
    API_URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWA-F1DEBC31-5694-4C1B-B8B3-50C0D59250B6&StationId={station_str}"

    data = []

    try:
        response = requests.get(API_URL)

        if response.status_code == 200:
            result = response.json()
            station_list = result['records']['Station']
            for station in station_list:
                time =station['ObsTime']['DateTime']
                clean_time = time[:19].replace("T", " ") # 取出前19個字元
                station_code = station['StationId']
                precp = check_miss_value(station['WeatherElement']['Now']['Precipitation'])
                wd = check_miss_value(station['WeatherElement']['WindDirection'])
                ws = check_miss_value(station['WeatherElement']['WindSpeed'])
                temp = check_miss_value(station['WeatherElement']['AirTemperature'])
                rh = check_miss_value(station['WeatherElement']['RelativeHumidity'])
                pressure = check_miss_value(station['WeatherElement']['AirPressure'])
                ws_gust = check_miss_value(station['WeatherElement']['GustInfo']['PeakGustSpeed'])
                wd_gust = check_miss_value(station['WeatherElement']['GustInfo']['Occurred_at']['WindDirection'])
                append_data = (clean_time, station_code, pressure, temp, rh, ws, wd, ws_gust, wd_gust, precp)
                data.append(append_data)
        
    except Exception as e:
        logging.error(f"無法提取資料，錯誤訊息：{type(e).__name__}：{e}")
    
    return data

def check_miss_value(val):
    if val in ["-99", "-99.0", "-999.0"]:
        val = None
    else:
        val = float(val)
    return val

if __name__ == '__main__':
    data = get_data_per_hour()
    df = pd.DataFrame(data, columns=['ObsTime', 'Station_Code', 'StnPres', 'Temperature', 'RH', 'WS', 'WD', 'WSGust', 'WDGust', 'Precp'])
    save_to_weather_db(df, 'data_per_hour', 'append')

