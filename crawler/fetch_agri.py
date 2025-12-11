import requests
import json
from datetime import date, timedelta
import logging
from database import init_db, insert_to_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_URL = 'https://data.moa.gov.tw/api/v1/AgriProductsTransType'

def fetch_cabbage_prices():

    logging.info("開始呼叫農產品交易行情API ...")

    yesterday = transfer_to_Taiwanese_year()
    page = 1
    continue_to_fetch = True
    is_stop_page = False
    data = []

    params = {
        "Start_time": "110.01.01",
        "End_time": f'{yesterday}',
        "CropCode": "LA1",
        "api_key": "3RAFHIV6Q9S60U0J08AKWTN227K1FE"
    }

    try:
        while continue_to_fetch:
            params['Page'] = page
            response = requests.get(API_URL, params=params)

            if response.status_code == 200:
                result = response.json()
                
                if "Data" and "Next" in result:
                    next_page = result["Next"]
                    data.extend(result["Data"])
                    logging.info(f"爬取第{page}頁成功，目前共{len(data)}筆資料")
                    print(data[page*1000-1000])

                    if next_page == True:
                        page += 1
                    else:
                        if result["Data"] != [] and not is_stop_page:
                            is_stop_page = True
                            continue
                        else:
                            continue_to_fetch = False

                else:
                    logging.error(f"發生預期外錯誤：{type(e).__name__}: {e}")
            else:
                logging.error(f"無法串接API，錯誤碼:{response.status_code}")
        logging.info(f"爬完資料了，共{len(data)}筆")

        if len(data) > 0:
            print("--- 第一筆資料 ---")
            print(json.dumps(data[0], indent=4, ensure_ascii=False)) #nsure_ascii=False 為了看到繁體中文
            
            price_str_to_float(data)
            
        else:
            logging.error("資料數為 0 ")

        return data
            
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
    else:
        logging.error(f"發生預期外錯誤：{type(e).__name__}: {e}")

def transfer_to_Taiwanese_year():
    yesterday = date.today() - timedelta(days=1)
    year = int(yesterday.year) - 1911

    yesterday = f'{year}.{yesterday.month:02d}.{yesterday.day:02d}'

    return yesterday

def price_str_to_float(data):
    for i in range(0, len(data)):
        data[i]['Upper_Price'] = float(data[i]['Upper_Price'])
        data[i]['Middle_Price'] = float(data[i]['Middle_Price'])
        data[i]['Lower_Price'] = float(data[i]['Lower_Price'])
        data[i]['Avg_Price'] = float(data[i]['Avg_Price'])
        data[i]['Trans_Quantity'] = float(data[i]['Trans_Quantity'])

if __name__ == '__main__':
    ROC_year_data = fetch_cabbage_prices()
    AD_data = transfer_to_AD(ROC_year_data)
    init_db()
    insert_to_db(AD_data)

    





