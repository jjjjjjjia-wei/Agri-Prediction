from sqlalchemy import create_engine
import logging
import weather_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_weather_data():
    DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_weather"
    }
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    db_engine = create_engine(db_url)

    return db_engine


def save_to_weather_db(weather_df, table):
    try:
        db_engine = get_weather_data()
        weather_df.to_sql(
            name = table,
            con = db_engine,
            if_exists = 'replace',
            index = False
        )
        logging.info('天氣資料寫入成功')

    except Exception as e:
        logging.error(f'天氣資料寫入失敗: {e}')

if __name__ == '__main__':
    weather_df = weather_csv.data_clean(weather_csv.merge())
    save_to_weather_db(weather_df, '2020-2025_original_weather')