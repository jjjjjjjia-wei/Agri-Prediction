from sqlalchemy import create_engine, text
import logging
import requests
from trans_database import save_to_db
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_transcation"
}

def init_veg_db():
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    db_engine = create_engine(db_url)

    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS market_rest_days(
    id INT AUTO_INCREMENT PRIMARY KEY,
    market_code VARCHAR(10) NOT NULL,
    market_name VARCHAR(10) NOT NULL,
    market_type VARCHAR(5) DEFAULT 'F',
    rest_date DATE NOT NULL,
    UNIQUE KEY uq_market_date (market_code, rest_date)
    );
'''
    with db_engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()

def fetch_market_rest_api():
    records = []
    API_URL = "https://data.moa.gov.tw/api/v1/MarketRestDayFarmWCF/"
    try:
        logging.info("開始呼叫各市場休市日API ...")

        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            result = response.json()

            # 解析API JSON檔
            for market in result.get("Data", []):
                m_code = market.get("MarkerNo")
                m_name = market.get("MarkerName")

                for type_item in market.get("MarketTypeList", []):
                    m_type = type_item.get("MarketType")
                    if m_type != 'F':
                        continue

                    for year_item in type_item.get("YearList", []):
                        roc_year = year_item.get("Year")
                        ad_year = int(roc_year) + 1911

                        if ad_year < 2020:
                            continue

                        for month_item in year_item.get("MonthList", []):
                            month = month_item.get("Month")
                            rest_days_str = month_item.get("Rest", "")
                            if not rest_days_str:
                                continue
                            # 解析日期字串 ex: "05、08"
                            days = rest_days_str.replace("、",",").replace(" ", "").split(',')

                            for day_str in days:
                                if day_str.isdigit():
                                    day = int(day_str)
                                    try:
                                        formatted_date = f"{ad_year:04d}-{month:02d}-{day:02d}"
                                        records.append({
                                            "market_code": m_code,
                                            "market_name": m_name,
                                            "market_type": m_type,
                                            "rest_date": formatted_date
                                        })
                                    except ValueError:
                                        logging.error(f"轉換發生錯誤: {ValueError}")
        else:
            logging.error(f"API請求失敗，狀態碼: {response.status_code}")

    except Exception as e:
        logging.error(f"介接市場休市日API出現問題：{type(e).__name__} => {e}")

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    init_veg_db()
    rest_df = fetch_market_rest_api()
    if not rest_df.empty:
        save_to_db(rest_df, "market_rest_days", if_exists='append')
    else:
        logging.warning("沒有抓取到任何休市資訊，不載入置資料庫")
