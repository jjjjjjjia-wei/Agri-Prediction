import pandas as pd
from trans_database import insert_to_veg_db

# 轉成西元年
def roc_to_western(str):
    parts = str.split('/')
    year = int(parts[0]) + 1911
    western_year = f'{year}-{parts[1]}-{parts[2]}'
    return western_year


if __name__ == "__main__":
    df = pd.read_excel('540_20210930-20241231.xls')
    df = df.dropna(subset=['TransDate'])
    df = df.sort_values(by='TransDate')
    df['TransDate'] = df['TransDate'].apply(roc_to_western) # 逐行應用
    print(df.head())
    data_for_insert = df.to_dict('records') # 把DataFrame轉成字典
    insert_to_veg_db(data_for_insert)

