# routers/predict.py
from fastapi import APIRouter, HTTPException
import pandas as pd

from database import predict_engine, trans_engine
from ml_models import get_market_model

router = APIRouter()

@router.get("/predict", tags=["價格預測"])
def predict_price(market_code: str):
    try:
        # --- 步驟 A: 去資料庫撈出該市場最新的一天特徵 ---
        sql = f"""
            SELECT * FROM merged_fe 
            WHERE MarketCode = '{market_code}' 
            ORDER BY TransDate DESC 
            LIMIT 1
        """
        latest_data = pd.read_sql(sql, predict_engine)
        
        if latest_data.empty:
            raise HTTPException(status_code=404, detail=f"找不到市場代碼 {market_code} 的特徵資料喔！")

        market_name = latest_data['MarketName'].iloc[0]
        data_date = latest_data['TransDate'].iloc[0].strftime('%Y-%m-%d')

        # --- 步驟 B: 清理特徵 ---
        drop_column = ['Avg_Price', 'TransDate', 'TcType', 'CropCode', 'CropName', 'MarketName', 'TTarget_Price', 'WTarget_Price']
        X_predict = latest_data.drop(columns=drop_column, errors='ignore')
        X_predict['MarketCode'] = X_predict['MarketCode'].astype('category')

        # --- 步驟 C: 動態取得該市場專屬的模型 ---
        try:
            t_model, w_model = get_market_model(market_code)
        except FileNotFoundError as fnf_err:
            raise HTTPException(status_code=404, detail=str(fnf_err))

        # --- 步驟 D: 開始預測 ---
        t_pred = round(float(t_model.predict(X_predict)[0]), 2)
        w_pred = round(float(w_model.predict(X_predict)[0]), 2)

        # --- 步驟 E: 撈取過去 7 天歷史價格進行高/低價比對 ---
        past_sql = f"""
            SELECT Avg_Price 
            FROM la1_clean 
            WHERE MarketCode = '{market_code}' 
            ORDER BY TransDate DESC 
            LIMIT 7
        """
        past_df = pd.read_sql(past_sql, trans_engine)

        t_alert = "正常"
        w_alert = "正常"

        if not past_df.empty:
            max_past = past_df['Avg_Price'].astype(float).max()
            min_past = past_df['Avg_Price'].astype(float).min()

            # 判斷明天預測價
            if t_pred >= max_past:
                t_alert = "週最高價"
            elif t_pred <= min_past:
                t_alert = "週最低價"

            # 判斷下週預測價
            if w_pred >= max_past:
                w_alert = "週最高價"
            elif w_pred <= min_past:
                w_alert = "週最低價"

        # --- 步驟 F: 端給客人 ---
        return {
            "市場名稱": market_name,
            "市場代碼": market_code,
            "特徵資料日期": data_date,
            "預測明天價格": t_pred,
            "預測明天提醒": t_alert,
            "預測下週價格": w_pred,
            "預測下週提醒": w_alert
        }

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))