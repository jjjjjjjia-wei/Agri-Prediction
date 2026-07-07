import xgboost as xgb
import os

# 此檔案的位置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

t_model_path = os.path.join(BASE_DIR, "model", "BT_cabbage_model.json")
w_model_path = os.path.join(BASE_DIR, "model", "BW_cabbage_model.json")

# --- 匯入訓練好的模型 ---
T_model = xgb.XGBRFRegressor()
T_model.load_model(t_model_path) # 預測明天的價格

W_model = xgb.XGBRFRegressor()
W_model.load_model(w_model_path) # 預測下禮拜的價格

print("two models are loading done !")