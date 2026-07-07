from fastapi import APIRouter, HTTPException
from database import trans_engine
import pandas as pd

router = APIRouter()

@router.get("/history_price", tags=['歷史菜價'])
def quary_history_price(market_code: str, start_date: str, end_date: str):
    try:
        # 處理多個市場代碼：將 "104,109" 轉成 "'104','109'"
        codes = market_code.split(',')
        market_list_str = "','".join(codes)
        
        # 🚨 關鍵修復：把 MarketCode 跟 Trans_Quantity 確實撈出來！
        sql = f"""
            SELECT TransDate, MarketCode, Avg_Price, Trans_Quantity 
            FROM la1_clean
            WHERE MarketCode IN ('{market_list_str}') 
            AND TransDate BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY TransDate ASC
        """
        
        history_data = pd.read_sql(sql, trans_engine)

        if history_data.empty:
             # 找不到資料時回傳空陣列，讓前端知道沒有資料，而不是直接噴錯
             return {"歷史數據": []}

        history_data['TransDate'] = pd.to_datetime(history_data['TransDate']).dt.strftime('%Y-%m-%d')
        
        # 確保數值是 Float 型態，前端圖表才畫得出來
        history_data['Avg_Price'] = history_data['Avg_Price'].astype(float)
        history_data['Trans_Quantity'] = history_data['Trans_Quantity'].astype(float)

        return {"歷史數據": history_data.to_dict(orient='records')}

    except Exception as e:
        print(f"SQL 錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"資料庫查詢出錯: {str(e)}")