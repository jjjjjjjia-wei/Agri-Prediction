import requests
import json
from datetime import date, timedelta
import logging
from trans_database import init_veg_db, insert_to_veg_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_URL = 'https://data.moa.gov.tw/api/v1/AgriProductsTransType'

def fetch_cabbage_prices(initial):

    logging.info("開始呼叫農產品交易行情API ...")

    today = transfer_to_Taiwanese_year('today')
    yesterday = transfer_to_Taiwanese_year('yesterday')
    before_yesterday = transfer_to_Taiwanese_year('before_yesterday')
    init_date = '109.01.01'
    page = 1
    continue_to_fetch = True
    is_stop_page = False
    data = []

    params = {
        "CropCode": "LA1",
        "api_key": "3RAFHIV6Q9S60U0J08AKWTN227K1FE"
    }

    try:
        while continue_to_fetch:
            if initial == 'yes':
                params['Start_time'] = init_date
                params['End_time'] = yesterday
            else:
                params['Start_time'] = before_yesterday
                params['End_time'] = today

            params['Page'] = page
            response = requests.get(API_URL, params=params)

            if response.status_code == 200:
                result = response.json()
                
                if "Data" in result and "Next" in result:
                    next_page = result["Next"]
                    data.extend(result["Data"])
                    logging.info(f"爬取第{page}頁成功，目前共{len(data)}筆資料")
                    print(data[page*1000-1000])

                    if next_page == True:
                        page += 1
                    else:
                        if result["Data"] != [] and not is_stop_page and page > 1:
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
            data.reverse()
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

def transfer_to_Taiwanese_year(day):
    today = date.today()
    yesterday = date.today() - timedelta(days=1)
    before_yesterday = date.today() - timedelta(days=2)
    
    today_year = int(today.year) - 1911
    yesterday_year = int(yesterday.year) - 1911
    before_yesterday_year = int(before_yesterday.year) - 1911

    today = f'{today_year}.{today.month:02d}.{today.day:02d}'
    yesterday = f'{yesterday_year}.{yesterday.month:02d}.{yesterday.day:02d}'
    before_yesterday = f'{before_yesterday_year}.{before_yesterday.month:02d}.{before_yesterday.day:02d}'

    if day == 'today':
        return today
    if day == 'yesterday':
        return yesterday
    if day == "before_yeaterday":
        return before_yesterday

def price_str_to_float(data):
    for i in range(0, len(data)):
        data[i]['Upper_Price'] = float(data[i]['Upper_Price'])
        data[i]['Middle_Price'] = float(data[i]['Middle_Price'])
        data[i]['Lower_Price'] = float(data[i]['Lower_Price'])
        data[i]['Avg_Price'] = float(data[i]['Avg_Price'])
        data[i]['Trans_Quantity'] = float(data[i]['Trans_Quantity'])

if __name__ == '__main__':
    is_initial = "no"
    ROC_year_data = fetch_cabbage_prices(initial=is_initial)
    AD_data = transfer_to_AD(ROC_year_data)
    init_veg_db()
    insert_to_veg_db(AD_data)

    





