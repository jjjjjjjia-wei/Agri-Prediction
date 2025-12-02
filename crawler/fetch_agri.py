import requests
import json
from datetime import datetime, timedelta
import logging

API_URL = 'https://data.moa.gov.tw/api/v1/AgriProductsTransType'

def fetch_cabbage_prices():
    logging.info("開始呼叫農產品交易行情API ...")

    params = {
        "Start_time": "114.11.15",
        "End_time": "114.11.18",
        "CropCode": "LA1"
    }

    try:
        response = requests.get(API_URL, params=params)

        if response.status_code == 200:
            result = response.json()
            if "Data" in result:
                data = result["Data"]

            logging.info(f"成功取得資料，共{len(data)}筆資料")

            if len(data) > 0:
                print("--- 第一筆資料 ---")
                print(json.dumps(data[0], indent=4, ensure_ascii=False)) #nsure_ascii=False 為了看到繁體中文
            else:
                logging.error("資料數為 0 ") 
        else:
            logging.error(f"請求失敗，錯誤代碼：{response.status_code}")
            
    except Exception as e:
        logging.error(f"發生預期外錯誤：{type(e).__name__}: {e}")


a = fetch_cabbage_prices()
