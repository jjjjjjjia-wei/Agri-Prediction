from sqlalchemy import create_engine
import pandas as pd
import numpy as np  # 引入 numpy 用來算 RMSE (對 MSE 開根號)
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def get_data():
    DB_CONFIG = {
        "host": "127.0.0.1",
        "port": "3306",
        "user": "root",
        "password": "willyylliw52",
        "database": "agri_merge"
    }
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    engine = create_engine(db_url)
    sql = 'SELECT * FROM merged_fe'
    return pd.read_sql(sql, engine)

def build_model(merged_df):
    merged_df['MarketCode'] = merged_df['MarketCode'].astype('category')

    # 先產生全域的 Target
    merged_df['TTarget_Price'] = merged_df.groupby('MarketCode')['Avg_Price'].shift(-1) 
    merged_df['WTarget_Price'] = merged_df.groupby('MarketCode')['Avg_Price'].shift(-7) 

    markets = merged_df['MarketCode'].unique()
    drop_column = ['Avg_Price', 'TransDate', 'TcType', 'CropCode', 'CropName', 'MarketName', 'TTarget_Price', 'WTarget_Price']

    n_estimators = [50, 100, 300]   # 資料量小，不需要到 1000 棵樹，幾百棵就足夠收斂
    learning_rate = [0.1, 0.05]
    max_depth = [3, 4, 5] # 調低樹深度，防止過擬合

    for market in markets:
        print(f"\n==================== 開始訓練市場：{market} ====================")
        
        market_df = merged_df[merged_df['MarketCode'] == market].copy()
        train_market = market_df[market_df['TransDate'] <= '2025-12-31'].copy()
        test_market = market_df[market_df['TransDate'] > '2025-12-31'].copy()

        target_configs = [
            {'col': 'TTarget_Price', 'label': 'tomorrow', 'best_score': 999.0},
            {'col': 'WTarget_Price', 'label': 'next_week', 'best_score': 999.0}
        ]

        for config in target_configs:
            target_col = config['col']
            label = config['label']
            best_score = config['best_score']

            print(f"\n--> 正在訓練 [{market}] 的 [{label}] 預測模型...")

            # 核心優化：分開清理 NaN，保留那珍貴的 7 天訓練資料！
            train_clean = train_market.dropna(subset=[target_col])
            test_clean = test_market.dropna(subset=[target_col])

            if len(train_clean) == 0 or len(test_clean) == 0:
                print(f"警告：市場 {market} 的 {label} 資料量不足，跳過訓練。")
                continue

            X_train = train_clean.drop(columns=drop_column)
            y_train = train_clean[target_col]
            X_test = test_clean.drop(columns=drop_column)
            y_test = test_clean[target_col]

            for n in n_estimators:
                for l in learning_rate:
                    for m in max_depth:
                        model = XGBRegressor(
                            n_estimators=n, 
                            learning_rate=l, 
                            max_depth=m,
                            subsample=0.8,             # 每次建樹只隨機抽 80% 的資料，防止死記特定樣本
                            colsample_bytree=0.8,      # 每次建樹只隨機抽 80% 的特徵，防止過度依賴「昨天的價格」
                            min_child_weight=3,        # 限制每個葉子節點最少要包含的樣本權重，低於 3 就不切分
                            random_state=42, 
                            enable_categorical=True,
                            tree_method='hist', 
                            device='cpu'       
                        )

                        model.fit(X_train, y_train)
                        predictions = model.predict(X_test)
                        train_predictions = model.predict(X_train)

                        # === 計算多維度模型效果公式 ===
                        train_mae = mean_absolute_error(y_true=y_train, y_pred=train_predictions)
                        mae = mean_absolute_error(y_true=y_test, y_pred=predictions)
                        mse = mean_squared_error(y_true=y_test, y_pred=predictions)
                        rmse = np.sqrt(mse) # 對 MSE 開根號得到 RMSE
                        r2 = r2_score(y_true=y_test, y_pred=predictions)

                        # 如果找到更低的 MAE，更新並記錄所有指標
                        if mae < best_score: 
                            best_score = mae
                            print(f'   [更新最佳模型] 參數 -> n_est: {n}, lr: {l}, depth: {m}')
                            print(f'   └── 指標效能 -> test_MAE: {mae:.4f} | train_MAE: {train_mae:.4f} | RMSE: {rmse:.4f} | MSE: {mse:.4f} | R²: {r2:.4f}')
                            
                            model_filename = f"{market}_{label}.json"
                            model.save_model(model_filename)

if __name__ == "__main__":
    df = get_data()
    build_model(df)