from sqlalchemy import create_engine
import logging
import weather_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_weather"
}

def save_to_db(weather_df):
    try:
        db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        db_engine = create_engine(db_url)
        weather_df.to_sql(
            name = '2020-2025_original_weather',
            con = db_engine,
            if_exists = 'replace',
            index = False
        )
        logging.info('寫入成功')

    except Exception as e:
        logging.error(f'寫入失敗: {e}')

if __name__ == '__main__':
    weather_df = weather_csv.data_clean(weather_csv.merge())
    save_to_db(weather_df)