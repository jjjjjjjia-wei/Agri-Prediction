from sqlalchemy import create_engine
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error


# 1. 從資料庫提取特徵工程完的資料
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

    merged_df = pd.read_sql(sql, engine)

    return merged_df

def build_model(merged_df):
    # 把 MarketCode 用上標籤
    merged_df['MarketCode'] = merged_df['MarketCode'].astype('category')

    train_df = merged_df[merged_df['TransDate'] <= '2025-12-31'].copy()
    test_df = merged_df[merged_df['TransDate'] > '2025-12-31'].copy()

    train_df['TTarget_Price'] = train_df.groupby('MarketCode')['Avg_Price'].shift(-2) # 明天的資料
    train_df['WTarget_Price'] = train_df.groupby('MarketCode')['Avg_Price'].shift(-8) # 下禮拜的資料
    test_df['TTarget_Price'] = test_df.groupby('MarketCode')['Avg_Price'].shift(-2)
    test_df['WTarget_Price'] = test_df.groupby('MarketCode')['Avg_Price'].shift(-8)

    drop_column = ['Avg_Price','TransDate' ,'TcType', 'CropCode', 'CropName', 'MarketName']

    # 訊練資料
    # 把沒有未來價格的最後兩天（Target_Price 為 NaN 的列）整筆刪除
    train_df = train_df.dropna(subset=['TTarget_Price', 'WTarget_Price'])
    test_df = test_df.dropna(subset=['TTarget_Price', 'WTarget_Price'])

    X_Ttrain = train_df.drop(columns=drop_column + ['TTarget_Price', 'WTarget_Price'])
    y_Ttrain = train_df['TTarget_Price']
    X_Wtrain = train_df.drop(columns=drop_column + ['TTarget_Price', 'WTarget_Price'])
    y_Wtrain = train_df['WTarget_Price']
    
    # 測試資料
    X_Ttest = test_df.drop(columns=drop_column + ['TTarget_Price', 'WTarget_Price'])
    y_Ttest = test_df['TTarget_Price']
    X_Wtest = test_df.drop(columns=drop_column + ['TTarget_Price', 'WTarget_Price'])
    y_Wtest = test_df['WTarget_Price']

    n_estimators = [100, 500, 1000]
    learning_rate = [0.1, 0.05, 0.01]
    max_depth = [6, 7, 8]
    T_best_score = 2.5
    W_best_score = 2.5
    for n in n_estimators:
        for l in learning_rate:
            for m in max_depth:
                T_model = XGBRegressor(
                    n_estimators=n, 
                    learning_rate=l, 
                    max_depth=m ,
                    random_state=42, 
                    enable_categorical=True,
                    tree_method='hist', # 啟用直方圖演算法
                    device='cpu'       
                    )
                W_model = XGBRegressor(
                    n_estimators=n, 
                    learning_rate=l, 
                    max_depth=m ,
                    random_state=42, 
                    enable_categorical=True,
                    tree_method='hist', # 啟用直方圖演算法
                    device='cpu'       
                    )

                T_model.fit(X_Ttrain,y_Ttrain)
                W_model.fit(X_Wtrain,y_Wtrain)

                T_predictions = T_model.predict(X_Ttest)
                W_predictions = W_model.predict(X_Wtest)

                # 測試準確率
                T_score = mean_absolute_error(y_true=y_Ttest, y_pred=T_predictions)
                W_score = mean_absolute_error(y_true=y_Wtest, y_pred=W_predictions)
                print(f"預測明天價格時，MSE：{T_score}")
                print(f"預測下禮拜價格時，MSE：{W_score}")

                if T_score < T_best_score: 
                       T_best_score = T_score
                       print(f'目前最佳模型MAE為：{T_best_score}, n_estimators:{n}, learning_rate:{l}, max_depth:{m}')
                       T_model.save_model("BT_cabbage_model.json")
                if W_score < W_best_score: 
                       W_best_score = W_score
                       print(f'目前最佳模型MAE為：{W_best_score}, n_estimators:{n}, learning_rate:{l}, max_depth:{m}')
                       W_model.save_model("BW_cabbage_model.json")


if __name__ == "__main__":
    df = get_data()
    build_model(df)