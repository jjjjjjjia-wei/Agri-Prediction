from datetime import timedelta, date


yesterday = date.today() - timedelta(days=1)
year = int(yesterday.year) - 1911

yesterday = f'{year}.{yesterday.month:02d}.{yesterday.day:02d}'

print(yesterday)