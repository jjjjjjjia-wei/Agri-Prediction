from sqlalchemy import text
import weather_database

# 1. 你的聰明字典：舊測站對應新測站
station_map = {
    'C0G870': 'C2G870',
    'C0G750': 'C0G940',  # 填寫你的第二個
    'C0K280': 'C2K280',  # 填寫你的第三個
    'C0K520': 'C0K590'   # 填寫你的第四個
}

engine = weather_database.get_weather_data()

with engine.connect() as conn:
    # 2. 抓出這張表目前「所有」的欄位名稱
    table_name = "2020-2025_all_stations_daily" # 記得換成你真實的表名
    result = conn.execute(text(f"SHOW COLUMNS FROM `{table_name}`"))
    columns = [row[0] for row in result]
    
    rename_statements = []
    
    # 3. 讓 Python 巡視每一個欄位，找出需要改名的
    for col in columns:
        for old_code, new_code in station_map.items():
            if old_code in col:
                # 幫舊欄位換新名字 (例如 C0G870_Temp -> C2G870_Temp)
                new_col = col.replace(old_code, new_code)
                # 記錄修改指令
                rename_statements.append(f"RENAME COLUMN `{col}` TO `{new_col}`")
                
    # 4. 把 52 個小指令，合併成一句超級 SQL 大指令！
    if rename_statements:
        alter_query = f"ALTER TABLE `{table_name}` {', '.join(rename_statements)};"
        
        print(f"準備執行的神級 SQL 語法：\n{alter_query}\n")
        
        # 執行！一秒鐘瞬間改完 52 個欄位
        conn.execute(text(alter_query))
        conn.commit() # 記得 commit 讓變更生效
        print("🎉 資料庫欄位名稱批次修改大成功！")
    else:
        print("沒有找到需要修改的欄位喔！")