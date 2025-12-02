from datetime import date

data = [{
    "TransDate": "114.11.18",
    "TcType": "N04",
    "CropCode": "LA1",
    "CropName": "甘藍-初秋",
    "MarketCode": "104",
    "MarketName": "台北二",
    "Upper_Price": 40.8,
    "Middle_Price": 21.6,
    "Lower_Price": 9.7,
    "Avg_Price": 23.1,
    "Trans_Quantity": 27000.0
},
{
    "TransDate": "114.11.18",
      "TcType": "N04",
      "CropCode": "LA1",
      "CropName": "甘藍-初秋",
      "MarketCode": "109",
      "MarketName": "台北一",
      "Upper_Price": 38.5,
      "Middle_Price": 19.6,
      "Lower_Price": 6,
      "Avg_Price": 20.7,
      "Trans_Quantity": 59827
    }]

for d in data:
    part = d['TransDate'].split('.')
    ROC_year = int(part[0])
    month = int(part[1])
    day = int(part[2])

    AD_year = ROC_year + 1911

    d['TransDate'] = date(AD_year, month, day)

print(data)