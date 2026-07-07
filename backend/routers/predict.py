# routers/predict.py
from fastapi import APIRouter, HTTPException
import pandas as pd

from database import predict_engine
from ml_models import T_model, W_model

# 建立預測部門的專屬路由器
router = APIRouter()

@router.get("/predict", tags=["價格預測"])
def predict_price(market_code: str):
    try:
        # --- 步驟 A: 去資料庫撈出該市場最新的一天 ---
        sql = f"""
            SELECT * FROM merged_fe 
            WHERE MarketCode = '{market_code}' 
            ORDER BY TransDate DESC 
            LIMIT 1
        """
        latest_data = pd.read_sql(sql, predict_engine)
        
        # 找不到資料的防呆機制
        if latest_data.empty:
            raise HTTPException(status_code=404, detail="找不到這個市場的資料喔！")

        # 用 iloc[0] 拆包裝，拿到乾淨的字串跟日期
        market_name = latest_data['MarketName'].iloc[0]
        data_date = latest_data['TransDate'].iloc[0].strftime('%Y-%m-%d')

        # --- 步驟 B: 清理特徵 ---
        drop_column = ['Avg_Price', 'TransDate', 'TcType', 'CropCode', 'CropName', 'MarketName', 'TTarget_Price', 'WTarget_Price']
        X_predict = latest_data.drop(columns=drop_column, errors='ignore')
        X_predict['MarketCode'] = X_predict['MarketCode'].astype('category')

        # --- 步驟 C: 請兩位大廚開始預測！ ---
        t_pred = T_model.predict(X_predict)[0]
        w_pred = W_model.predict(X_predict)[0]

        # --- 步驟 D: 端給客人 ---
        return {
            "市場名稱": market_name,
            "市場代碼": market_code,
            "特徵資料日期": data_date,
            "預測明天價格": round(float(t_pred), 2),
            "預測下週價格": round(float(w_pred), 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))