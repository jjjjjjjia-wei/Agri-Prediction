import pandas as pd
import logging
from trans_database import get_trans_data, save_to_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

all_market_code = ['104','109','220','241','260','338','400','420','512',
                   '514','540','648','800','830','900','930','950']

def clean():
    sql = f'SELECT * FROM agri_transcation.la1_clean'
    engine = get_trans_data()
    df = pd.read_sql(sql, engine)
    
    clean_column = ['Upper_Price', 'Middle_Price', 'Lower_Price', 'Avg_Price', 'Trans_Quantity']

    # --- 1. 處理缺失值 ---
    df[clean_column] = df.groupby('MarketCode')[clean_column].transform(lambda x: x.interpolate())

    # --- 2. 處理重複值 ---
    repeat = df.duplicated().sum()
    if repeat != 0:
        df.drop_duplicates(inplace=True)
    
    # --- 3. 處理異常值 ---
    #print("資料異常值處理前")
    #print(df.describe().T) # 檢查資料分布
    # 把為0.0的上價 中價 底價去掉，並更新，依據中價=(上價+下價)/2
    df.loc[df['Upper_Price']==0.0, 'Upper_Price'] = df['Middle_Price']*2 - df['Lower_Price']     
    df.loc[df['Middle_Price']==0.0, 'Middle_Price'] = (df['Upper_Price'] + df['Lower_Price']) / 2
    df.loc[df['Lower_Price']==0.0, 'Lower_Price'] = df['Middle_Price']*2 - df['Upper_Price']
    # 檢查是否上價>中價>下價
    df.loc[df['Upper_Price']<df['Middle_Price'], ['Upper_Price', 'Middle_Price']] = df.loc[df['Upper_Price']<df['Middle_Price'], ['Middle_Price', 'Upper_Price']].values
    df.loc[df['Upper_Price']<df['Lower_Price'], ['Upper_Price', 'Lower_Price']] = df.loc[df['Upper_Price']<df['Lower_Price'], ['Lower_Price', 'Upper_Price']].values
    df.loc[df['Middle_Price']<df['Lower_Price'], ['Middle_Price', 'Lower_Price']] = df.loc[df['Middle_Price']<df['Lower_Price'], ['Lower_Price', 'Middle_Price']].values
    # 檢查是否 上價>平均價 AND 下價<平均價
    if df[(df['Upper_Price']<df['Avg_Price']) | (df['Avg_Price']<df['Lower_Price'])].empty:
        print('上價>平均價 AND 下價<平均價 check ok!')
    
    return df



if __name__ == "__main__":
    df = clean()
    # df.info()
    save_to_db(df, 'la1_clean')