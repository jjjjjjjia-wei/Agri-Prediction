from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import os

# 設定 Matplotlib 字體（確保英文與符號美觀，並避免負號顯示異常）
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

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

def plot_time_series_comparison(dates, y_true, y_pred, market, label, metrics):
    """繪製真實值與預測值的時序對比圖（展現極端價格波動捕捉能力）"""
    plt.figure(figsize=(12, 5), dpi=300)
    
    # 繪製真實價格與預測價格折線
    plt.plot(dates, y_true, label='Actual Price', color='#1f77b4', linewidth=1.8, alpha=0.9)
    plt.plot(dates, y_pred, label='Predicted Price', color='#ff7f0e', linewidth=1.5, linestyle='--', alpha=0.85)
    
    # 設置圖表標題與軸標籤
    title_label = label.replace('_', ' ').title()
    plt.title(f'[{market}] Market Cabbage Price Forecasting ({title_label}) - Actual vs. Predicted', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Date', fontsize=10)
    plt.ylabel('Price (NTD/kg)', fontsize=10)
    
    # 圖例與網格設定
    plt.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    # 在圖面上加上模型的核心評估數據面板
    metrics_text = (f"R²: {metrics['r2']:.4f}\n"
                    f"MAE: {metrics['test_mae']:.2f} NTD/kg\n"
                    f"RMSE: {metrics['rmse']:.2f} NTD/kg")
    
    plt.gca().text(0.02, 0.93, metrics_text, transform=plt.gca().transAxes,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='whitesmoke', alpha=0.85, edgecolor='lightgray'))
    
    plt.tight_layout()
    
    # 自動建立輸出的資料夾並儲存圖檔
    os.makedirs('ts_plots', exist_ok=True)
    img_filename = f"ts_plots/{market}_{label}_timeseries.png"
    plt.savefig(img_filename, dpi=300)
    plt.close()
    print(f'   └── 📸 已儲存時序預測對比圖表：{img_filename}')

def build_model(merged_df):
    # 1. 基本資料整理
    merged_df['TransDate'] = pd.to_datetime(merged_df['TransDate'])
    merged_df = merged_df.sort_values(
        ['MarketCode', 'TransDate']
    ).reset_index(drop=True)

    markets = merged_df['MarketCode'].unique()

    TRAIN_END = pd.Timestamp('2024-12-31')
    VAL_END = pd.Timestamp('2025-12-31')

    # 超參數搜尋空間
    n_estimators = [50, 100]
    learning_rate = [0.05, 0.03]
    max_depth = [3, 4]

    for market in markets:
        print(
            f"\n==================== "
            f"開始訓練市場：{market} "
            f"===================="
        )

        market_df = merged_df[
            merged_df['MarketCode'] == market
        ].copy()

        # 2. 建立不同 forecasting horizon 的 Target
        market_df['TTarget_Price'] = (
            market_df['Avg_Price'].shift(-1)
        )
        market_df['3DTarget_Price'] = (
            market_df['Avg_Price'].shift(-3)
        )
        market_df['WTarget_Price'] = (
            market_df['Avg_Price'].shift(-7)
        )

        # 同時保存 Target 所對應的日期
        # 用來避免 train / val / test 邊界洩漏
        market_df['TTarget_Date'] = (
            market_df['TransDate'].shift(-1)
        )
        market_df['3DTarget_Date'] = (
            market_df['TransDate'].shift(-3)
        )
        market_df['WTarget_Date'] = (
            market_df['TransDate'].shift(-7)
        )

        target_configs = [
            {
                'col': 'TTarget_Price',
                'date_col': 'TTarget_Date',
                'label': 'tomorrow'
            },
            {
                'col': '3DTarget_Price',
                'date_col': '3DTarget_Date',
                'label': 'three_days'
            },
            {
                'col': 'WTarget_Price',
                'date_col': 'WTarget_Date',
                'label': 'next_week'
            }
        ]

        drop_columns = [
            'TransDate',
            'TcType',
            'CropCode',
            'CropName',
            'MarketName',
            'MarketCode',

            'TTarget_Price',
            '3DTarget_Price',
            'WTarget_Price',

            'TTarget_Date',
            '3DTarget_Date',
            'WTarget_Date'
        ]

        for config in target_configs:

            target_col = config['col']
            target_date_col = config['date_col']
            label = config['label']

            print(
                f"\n--> 正在尋優 [{market}] "
                f"的 [{label}] 預測模型..."
            )

            # 3. 時間切分

            # Train：
            # Target 日期不能超過 2024/12/31
            train_clean = market_df[
                market_df[target_date_col] <= TRAIN_END
            ].dropna(
                subset=[target_col, target_date_col]
            ).copy()

            # Validation：
            # Feature 日期在 2025，
            # Target 日期也必須仍在 2025
            val_clean = market_df[
                (market_df['TransDate'] > TRAIN_END) &
                (market_df[target_date_col] <= VAL_END)
            ].dropna(
                subset=[target_col, target_date_col]
            ).copy()

            # Test：
            # Feature 日期在 2026 以後
            test_clean = market_df[
                market_df['TransDate'] > VAL_END
            ].dropna(
                subset=[target_col, target_date_col]
            ).copy()

            if (
                len(train_clean) == 0
                or len(val_clean) == 0
                or len(test_clean) == 0
            ):
                print(
                    f"警告：市場 {market} 的 {label} "
                    f"Train/Validation/Test 資料不足，跳過。"
                )
                continue

            feature_cols_to_drop = [
                c for c in drop_columns
                if c in market_df.columns
            ]

            X_train = train_clean.drop(
                columns=feature_cols_to_drop
            )
            y_train = train_clean[target_col]

            X_val = val_clean.drop(
                columns=feature_cols_to_drop
            )
            y_val = val_clean[target_col]

            X_test = test_clean.drop(
                columns=feature_cols_to_drop
            )
            y_test = test_clean[target_col]

            test_dates = test_clean['TransDate']

            # =========================
            # 4. Validation Grid Search
            # =========================

            best_val_mae = float('inf')
            best_params = None

            for n in n_estimators:
                for lr in learning_rate:
                    for depth in max_depth:

                        model = XGBRegressor(
                            n_estimators=n,
                            learning_rate=lr,
                            max_depth=depth,
                            subsample=0.8,
                            colsample_bytree=0.35,
                            min_child_weight=5,
                            reg_alpha=1.0,
                            reg_lambda=2.0,
                            random_state=42,
                            enable_categorical=True,
                            tree_method='hist',
                            device='cpu'
                        )

                        model.fit(
                            X_train,
                            y_train
                        )

                        val_predictions = model.predict(
                            X_val
                        )

                        val_mae = mean_absolute_error(
                            y_val,
                            val_predictions
                        )

                        if val_mae < best_val_mae:
                            best_val_mae = val_mae
                            best_params = {
                                'n_estimators': n,
                                'learning_rate': lr,
                                'max_depth': depth
                            }

            if best_params is None:
                print(
                    f"警告：[{market}] [{label}] "
                    f"無法找到最佳參數。"
                )
                continue

            print(
                f"   [最佳 Validation 參數] "
                f"n_est={best_params['n_estimators']}, "
                f"lr={best_params['learning_rate']}, "
                f"depth={best_params['max_depth']}, "
                f"val_MAE={best_val_mae:.4f}"
            )

            # =========================
            # 5. Train + Validation
            #    使用最佳參數重新訓練
            # =========================

            train_val_clean = pd.concat(
                [train_clean, val_clean],
                axis=0
            ).sort_values('TransDate')

            X_train_val = train_val_clean.drop(
                columns=feature_cols_to_drop
            )
            y_train_val = train_val_clean[target_col]

            final_model = XGBRegressor(
                n_estimators=best_params['n_estimators'],
                learning_rate=best_params['learning_rate'],
                max_depth=best_params['max_depth'],
                subsample=0.8,
                colsample_bytree=0.35,
                min_child_weight=5,
                reg_alpha=1.0,
                reg_lambda=2.0,
                random_state=42,
                enable_categorical=True,
                tree_method='hist',
                device='cpu'
            )

            final_model.fit(
                X_train_val,
                y_train_val
            )

            # =========================
            # 6. Test：
            #    最後才使用一次
            # =========================

            test_predictions = final_model.predict(
                X_test
            )

            train_predictions = final_model.predict(
                X_train_val
            )

            test_mae = mean_absolute_error(
                y_test,
                test_predictions
            )

            test_mse = mean_squared_error(
                y_test,
                test_predictions
            )

            test_rmse = np.sqrt(test_mse)

            test_r2 = r2_score(
                y_test,
                test_predictions
            )

            train_mae = mean_absolute_error(
                y_train_val,
                train_predictions
            )

            final_metrics = {
                'params': best_params,
                'validation_mae': best_val_mae,
                'test_mae': test_mae,
                'train_mae': train_mae,
                'rmse': test_rmse,
                'mse': test_mse,
                'r2': test_r2
            }

            print(
                f"   └── 最終 Test 效能 -> "
                f"MAE: {test_mae:.4f} | "
                f"RMSE: {test_rmse:.4f} | "
                f"R²: {test_r2:.4f}"
            )

            # =========================
            # 7. 儲存 final model
            # =========================

            model_filename = (
                f"{market}_{label}.json"
            )

            final_model.save_model(
                model_filename
            )

            # =========================
            # 8. Test 時序圖
            # =========================

            plot_time_series_comparison(
                dates=test_dates,
                y_true=y_test,
                y_pred=test_predictions,
                market=market,
                label=label,
                metrics=final_metrics
            )

if __name__ == "__main__":
    df = get_data()
    build_model(df)