import requests
import json
from datetime import date
import logging
import mysql.connector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_URL = 'https://data.moa.gov.tw/api/v1/AgriProductsTransType'

def fetch_cabbage_prices():

    logging.info("開始呼叫農產品交易行情API ...")

    params = {
        "Start_time": "110.01.01",
        "End_time": "114.12.06",
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

            return data
         
        else:
            logging.error(f"請求失敗，錯誤代碼：{response.status_code}")
            
    except Exception as e:
        logging.error(f"發生預期外錯誤：{type(e).__name__}: {e}")


def transfer_to_AD(data):
    if len(data) > 0:
        try:
            for d in data:
                part = d['TransDate'].split('.')
                ROC_year = int(part[0])
                month = int(part[1])
                day = int(part[2])

                AD_year = ROC_year + 1911

                d['TransDate'] = date(AD_year, month, day)

            return data 
                
        except Exception as e:
            logging.error(f"發生預期外錯誤：{type(e).__name__}: {e}")     





