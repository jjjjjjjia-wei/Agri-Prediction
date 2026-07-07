from sqlalchemy import create_engine

# --- 設定 預測 MySQL 資料庫 ---
DB_CONFIG_predict = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52", # 你的資料庫密碼
    "database": "agri_merge"
}

predict_db_url = f"mysql+pymysql://{DB_CONFIG_predict['user']}:{DB_CONFIG_predict['password']}@{DB_CONFIG_predict['host']}:{DB_CONFIG_predict['port']}/{DB_CONFIG_predict['database']}"
predict_engine = create_engine(predict_db_url)

# --- 設定 天氣 MySQL 資料庫 ---
DB_CONFIG_wea = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_wewather"
}

wea_db_url = f"mysql+pymysql://{DB_CONFIG_wea['user']}:{DB_CONFIG_wea['password']}@{DB_CONFIG_wea['host']}:{DB_CONFIG_wea['port']}/{DB_CONFIG_wea['database']}"
wea_engine = create_engine(wea_db_url)

# --- 設定 交易行情 MySQL 資料庫 ---
DB_CONFIG_tras = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_transcation"
}

trans_db_url = f"mysql+pymysql://{DB_CONFIG_tras['user']}:{DB_CONFIG_tras['password']}@{DB_CONFIG_tras['host']}:{DB_CONFIG_tras['port']}/{DB_CONFIG_tras['database']}"
trans_engine = create_engine(trans_db_url)

