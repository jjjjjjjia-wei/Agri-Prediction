import os
from xgboost import XGBRegressor

# 此檔案的位置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model") # 模型的位置

# 用來快取已載入的模型，防止多次載入
loaded_models = {}

def get_market_model(market_code: str):
    t_model_key = f"{market_code}_tomorrow"
    w_model_key = f"{market_code}_next_week"

    # 如果還沒有載入過明日預測模型，就先載入
    if t_model_key not in loaded_models:
        t_path = os.path.join(MODEL_DIR, f'{t_model_key}.json')
        if not os.path.exists(t_path):
            raise FileNotFoundError(f"找不到市場 {market_code} 的明日預測模型：{t_path}")
        t_model = XGBRegressor()
        t_model.load_model(t_path)
        loaded_models[t_model_key] = t_model

    if w_model_key not in loaded_models:
        w_path = os.path.join(MODEL_DIR, f"{w_model_key}.json")
        if not os.path.exists(w_path):
            raise FileNotFoundError(f"找不到市場 {market_code} 的下週預測模型：{w_path}")
        w_model = XGBRegressor()
        w_model.load_model(w_path)
        loaded_models[w_model_key] = w_model

    return loaded_models[t_model_key], loaded_models[w_model_key]