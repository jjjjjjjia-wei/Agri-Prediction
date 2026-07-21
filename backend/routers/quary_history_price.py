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
        
        # 查詢該日期區間，是否有市場休息
        rest_sql = f'''
            SELECT DISTINCT market_code, rest_date
            FROM market_rest_days
            WHERE market_code IN ('{market_list_str}')
            AND rest_date BETWEEN '{start_date}' AND '{end_date}'
        '''
        rest_df = pd.read_sql(rest_sql, trans_engine)
        
        # 整理出休市的市場代碼清單與日期清單
        rest_dates = rest_df['rest_date'].astype(str).tolist() if not rest_df.empty else []
        
        # 查詢歷史價格
        sql = f"""
            SELECT TransDate, MarketCode, Avg_Price, Trans_Quantity 
            FROM la1_clean
            WHERE MarketCode IN ('{market_list_str}') 
            AND TransDate BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY TransDate ASC
        """
        
        history_data = pd.read_sql(sql, trans_engine)

        # 格式轉換
        if not history_data.empty:
            history_data['TransDate'] = pd.to_datetime(history_data['TransDate']).dt.strftime('%Y-%m-%d')
            history_data['Avg_Price'] = history_data['Avg_Price'].astype(float)
            history_data['Trans_Quantity'] = history_data['Trans_Quantity'].astype(float)
            data_list = history_data.to_dict(orient='records')
        else:
            data_list = []

        # 回傳給前端
        is_single_day = (start_date == end_date)
        is_rest_day = is_single_day and (len(rest_dates)>0)

        return {
            "is_rest_day": is_rest_day, # True表示所選的市場休市
            "rest_dates": rest_dates, # 休市日期清單
            "歷史數據": data_list
        }

    except Exception as e:
        print(f"SQL 錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"資料庫查詢出錯: {str(e)}")