from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import os

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
    
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    return df

def plot_feature_importance(model, feature_names, market, label, top_n=15):
    """繪製並輸出特徵重要性橫向長條圖"""
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values('Importance', ascending=False).head(top_n)

    plt.figure(figsize=(10, 6))
    plt.barh(importance_df['Feature'][::-1], importance_df['Importance'][::-1], color='skyblue', edgecolor='navy')
    plt.title(f'[{market}] market [{label}] predict - Top {top_n} Feature Importance')
    plt.xlabel('Importance score (Gain / Weight)')
    plt.tight_layout()
    
    img_filename = f"{market}_{label}_importance.png"
    plt.savefig(img_filename, dpi=300)
    plt.close()
    print(f'   └── 📸 已儲存最佳模型特徵重要性圖表：{img_filename}')

def build_model(merged_df):
    # 強制轉換時間格式並進行嚴格排序，避免 shift() 錯位
    merged_df['TransDate'] = pd.to_datetime(merged_df['TransDate'])
    merged_df = merged_df.sort_values(['MarketCode', 'TransDate']).reset_index(drop=True)

    markets = merged_df['MarketCode'].unique()
    
    drop_column = ['Avg_Price', 'TransDate', 'TcType', 'CropCode', 'CropName', 'MarketName', 'MarketCode', 
                   'TTarget_Price', '3DTarget_Price', 'WTarget_Price']

    n_estimators = [50, 100]
    learning_rate = [0.05, 0.03]
    max_depth = [3, 4]

    for market in markets:
        print(f"\n==================== 開始訓練市場：{market} ====================")
        market_df = merged_df[merged_df['MarketCode'] == market].copy()

        # 按市場獨立產生 Target，確保 shift 邏輯正確
        market_df['TTarget_Price'] = market_df['Avg_Price'].shift(-1)  # 明天
        market_df['3DTarget_Price'] = market_df['Avg_Price'].shift(-3) # 三天後
        market_df['WTarget_Price'] = market_df['Avg_Price'].shift(-7)  # 下週

        # 以時間切分訓練與測試集
        train_market = market_df[market_df['TransDate'] <= '2025-12-31'].copy()
        test_market = market_df[market_df['TransDate'] > '2025-12-31'].copy()

        target_configs = [
            {'col': 'TTarget_Price', 'label': 'tomorrow'},
            {'col': '3DTarget_Price', 'label': 'three_days'},
            {'col': 'WTarget_Price', 'label': 'next_week'}
        ]

        for config in target_configs:
            target_col = config['col']
            label = config['label']

            print(f"\n--> 正在尋優 [{market}] 的 [{label}] 預測模型...")

            train_clean = train_market.dropna(subset=[target_col])
            test_clean = test_market.dropna(subset=[target_col])

            if len(train_clean) == 0 or len(test_clean) == 0:
                print(f"警告：市場 {market} 的 {label} 資料量不足，跳過訓練。")
                continue

            X_train = train_clean.drop(columns=[c for c in drop_column if c in train_clean.columns])
            y_train = train_clean[target_col]
            X_test = test_clean.drop(columns=[c for c in drop_column if c in test_clean.columns])
            y_test = test_clean[target_col]

            # 引入暫存變數，尋找全域最佳模型後再統一存檔/畫圖
            best_mae = float('inf')
            best_model = None
            best_metrics = {}

            for n in n_estimators:
                for l in learning_rate:
                    for m in max_depth:
                        model = XGBRegressor(
                            n_estimators=n, 
                            learning_rate=l, 
                            max_depth=m,
                            subsample=0.7,
                            colsample_bytree=0.5,
                            min_child_weight=5,
                            reg_alpha=0.5,
                            reg_lambda=1.5,
                            random_state=42, 
                            enable_categorical=True,
                            tree_method='hist', 
                            device='cpu'       
                        )

                        model.fit(X_train, y_train)
                        predictions = model.predict(X_test)
                        train_predictions = model.predict(X_train)

                        mae = mean_absolute_error(y_true=y_test, y_pred=predictions)

                        if mae < best_mae: 
                            best_mae = mae
                            mse = mean_squared_error(y_true=y_test, y_pred=predictions)
                            best_metrics = {
                                'params': (n, l, m),
                                'test_mae': mae,
                                'train_mae': mean_absolute_error(y_true=y_train, y_pred=train_predictions),
                                'rmse': np.sqrt(mse),
                                'mse': mse,
                                'r2': r2_score(y_true=y_test, y_pred=predictions)
                            }
                            best_model = model

            # 迴圈結束後，僅對該市場與目標的「最佳模型」進行一次性儲存與繪圖
            if best_model is not None:
                p = best_metrics['params']
                print(f"   [最佳模型] 參數 -> n_est: {p[0]}, lr: {p[1]}, depth: {p[2]}")
                print(f"   └── 指標效能 -> test_MAE: {best_metrics['test_mae']:.4f} | train_MAE: {best_metrics['train_mae']:.4f} | RMSE: {best_metrics['rmse']:.4f} | MSE: {best_metrics['mse']:.4f} | R²: {best_metrics['r2']:.4f}")
                
                # 儲存 JSON 模型檔
                model_filename = f"{market}_{label}.json"
                best_model.save_model(model_filename)

                # 繪製特徵重要性圖表
                plot_feature_importance(best_model, X_train.columns, market, label, top_n=15)

if __name__ == "__main__":
    df = get_data()
    build_model(df)