import mysql.connector
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port="3306",
            user="root",
            password="willyylliw52"
        )
        cursor = conn.cursor()

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS LA1 (
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
            `Trans_Quantity` INT NOT NULL(

            INDEX idx_transdate (TransDate),
            INDEX idx_crop (CropCode)
        );        
        """

        cursor.execute(create_table_sql)
        logging.info("資料庫建立完成")

    except Exception as e:
        logging.error(f'發生預期外錯誤: {type(e).__name__}: {e}')
    
    finally:
        if 'mydb' in locals() and conn.is_connected():
            cursor.close()
            conn.close()



    