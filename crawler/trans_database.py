import mysql.connector
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "3306",
    "user": "root",
    "password": "willyylliw52",
    "database": "agri_transcation"
}

def init_veg_db():
    # 初始化變數，避免 finally 出錯
    conn = False
    cursor = False
    try:
        conn = mysql.connector.connect(**DB_CONFIG) #**讓字典變成key=value的樣子
        cursor = conn.cursor()

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS la1 (
            `ID` INT AUTO_INCREMENT PRIMARY KEY,
            `TransDate` DATE NOT NULL,
            `TcType` VARCHAR(10),
            `CropCode` VARCHAR(10) NOT NULL,
            `CropName` VARCHAR(10),
            `MarketCode` VARCHAR(10),
            `MarketName` VARCHAR(10),
            `Upper_Price` FLOAT NOT NULL,
            `Middle_Price` FLOAT NOT NULL,
            `Lower_Price` FLOAT NOT NULL,
            `Avg_Price` FLOAT NOT NULL,
            `Trans_Quantity` FLOAT NOT NULL,

            INDEX idx_transdate (TransDate),
            INDEX idx_crop (CropCode),
            UNIQUE INDEX unique_data(TransDate, CropCode, MarketCode)
        );        
        """
        cursor.execute(create_table_sql)
        logging.info("資料庫建立完成")

    except Exception as e:
        logging.error(f'發生預期外錯誤: {type(e).__name__}: {e}')
    
    finally:
        if conn and conn.is_connected(): #卻保有成功建立變數 conn 且連線是活著狀態
            if cursor: 
                cursor.close()
            conn.close()


def insert_to_veg_db(list_data):
    conn = False
    try:
        logging.info("開始連接資料庫...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("資料庫連接完成!")

        sql = """INSERT IGNORE INTO la1 (TransDate, TcType, CropCode, CropName, MarketCode, MarketName, Upper_Price, Middle_Price, Lower_Price, Avg_Price, Trans_Quantity) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        # 將 Dict 列表轉換為 Tuple 列表
        # 因為 executemany 用 %s 時不支援直接傳入 Dict
        values_to_insert = []
        for d in list_data:
            values_to_insert.append((
                d['TransDate'],
                d.get('TcType'),
                d.get('CropCode'),
                d.get('CropName'),
                d.get('MarketCode'),
                d.get('MarketName'),
                d.get('Upper_Price'),
                d.get('Middle_Price'),
                d.get('Lower_Price'),
                d.get('Avg_Price'),
                d.get('Trans_Quantity')
            ))

        logging.info(f"開始插入數據，共{len(values_to_insert)}筆資料...")
        cursor.executemany(sql, values_to_insert)

        conn.commit() # 一定要加上這行，否則不會有任何改變
        logging.info("插入完成!")

    except Exception as e:
        logging.error(f"發生預期外錯誤{type(e).__name__}:{e}")
    
    finally:
        if conn and conn.is_connected():
            if cursor: cursor.close()
            conn.close()





    