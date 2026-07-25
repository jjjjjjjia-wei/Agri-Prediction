# routers/predict.py
from fastapi import APIRouter, HTTPException
import pandas as pd
from datetime import datetime, timedelta
import traceback

from database import predict_engine, trans_engine
from ml_models import get_market_model

router = APIRouter()

@router.get("/predict", tags=["價格預測"])
def predict_price(market_code: str):
    try:
        # --- 步驟 A: 撈取最新特徵資料 ---
        sql = f"""
            SELECT * FROM merged_fe 
            WHERE MarketCode = '{market_code}' 
            ORDER BY TransDate DESC 
            LIMIT 1
        """
        latest_data = pd.read_sql(sql, predict_engine)
        
        if latest_data.empty:
            raise HTTPException(status_code=404, detail=f"找不到市場代碼 {market_code} 的特徵資料！")

        market_name = latest_data['MarketName'].iloc[0]
        latest_trans_date = pd.to_datetime(latest_data['TransDate'].iloc[0])
        data_date = latest_trans_date.strftime('%Y-%m-%d')

        # --- 步驟 B: 清理特徵 ---
        drop_column = [
            'Avg_Price', 'TransDate', 'TcType', 'CropCode', 'CropName', 
            'MarketName', 'MarketCode', 'TTarget_Price', '3DTarget_Price', 'WTarget_Price'
        ]
        X_predict = latest_data.drop(columns=[c for c in drop_column if c in latest_data.columns], errors='ignore')

        # --- 步驟 C: 取得專屬模型 ---
        try:
            t_model, three_day_model, w_model = get_market_model(market_code)
        except FileNotFoundError as fnf_err:
            raise HTTPException(status_code=404, detail=str(fnf_err))

        # --- 步驟 D: 進行預測 ---
        t_pred = round(float(t_model.predict(X_predict)[0]), 2)
        three_day_pred = round(float(three_day_model.predict(X_predict)[0]), 2)
        w_pred = round(float(w_model.predict(X_predict)[0]), 2)

        # --- 步驟 E: 撈取過去 5 天歷史真實價格 ---
        trend_chart_data = []
        last_real_price = None

        try:
            past_5_sql = f"""
                SELECT TransDate, Avg_Price 
                FROM la1_clean 
                WHERE MarketCode = '{market_code}' 
                ORDER BY TransDate DESC 
                LIMIT 5
            """
            past_5_df = pd.read_sql(past_5_sql, trans_engine)
            
            if not past_5_df.empty:
                past_5_df = past_5_df.sort_values('TransDate').reset_index(drop=True)
                for idx, row in past_5_df.iterrows():
                    d_str = pd.to_datetime(row['TransDate']).strftime('%Y-%m-%d')
                    p_val = round(float(row['Avg_Price']), 2)
                    trend_chart_data.append({
                        "date": d_str,
                        "actual_price": p_val,
                        "predict_price": None,
                        "type": "history"
                    })
                last_real_price = trend_chart_data[-1]["actual_price"]
        except Exception as db_e:
            print(f"⚠️ 歷史資料撈取警告 (可忽略但不影響預測): {db_e}")

        # --- 步驟 F: 構建趨勢圖資料點 ---
        date_t1 = (latest_trans_date + timedelta(days=1)).strftime('%Y-%m-%d')
        date_t3 = (latest_trans_date + timedelta(days=3)).strftime('%Y-%m-%d')
        date_t7 = (latest_trans_date + timedelta(days=7)).strftime('%Y-%m-%d')

        if last_real_price is not None and len(trend_chart_data) > 0:
            trend_chart_data[-1]["predict_price"] = last_real_price

        trend_chart_data.append({"date": f"{date_t1} (明日)", "actual_price": None, "predict_price": t_pred, "type": "predict"})
        trend_chart_data.append({"date": f"{date_t3} (3天後)", "actual_price": None, "predict_price": three_day_pred, "type": "predict"})
        trend_chart_data.append({"date": f"{date_t7} (下週)", "actual_price": None, "predict_price": w_pred, "type": "predict"})

        # --- 步驟 G: 價格警示邏輯 ---
        t_alert = "正常"
        w_alert = "正常"

        try:
            past_7_sql = f"""
                SELECT Avg_Price FROM la1_clean 
                WHERE MarketCode = '{market_code}' 
                ORDER BY TransDate DESC LIMIT 7
            """
            past_7_df = pd.read_sql(past_7_sql, trans_engine)

            if not past_7_df.empty:
                max_past = past_7_df['Avg_Price'].astype(float).max()
                min_past = past_7_df['Avg_Price'].astype(float).min()

                if t_pred >= max_past: t_alert = "週最高價"
                elif t_pred <= min_past: t_alert = "週最低價"

                if w_pred >= max_past: w_alert = "週最高價"
                elif w_pred <= min_past: w_alert = "週最低價"
        except Exception:
            pass

        return {
            "市場名稱": market_name,
            "市場代碼": market_code,
            "特徵資料日期": data_date,
            "預測明天價格": t_pred,
            "預測明天提醒": t_alert,
            "預測三天後價格": three_day_pred,
            "預測下週價格": w_pred,
            "預測下週提醒": w_alert,
            "趨勢圖資料": trend_chart_data
        }

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        # 🎯 關鍵：印出詳細的報錯行數與原因到 Uvicorn Terminal
        print("\n================ 🚨 API 500 錯誤詳情 🚨 ================")
        traceback.print_exc()
        print("========================================================\n")
        raise HTTPException(status_code=500, detail=f"伺服器內部錯誤：{str(e)}")