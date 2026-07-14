import hmac
import hashlib
import time
import requests
import os
from dotenv import load_dotenv
from BB import ByBit
import datetime
from datetime import datetime
import json



bybit = ByBit(demo=True)

response = bybit._req("GET", "/v5/market/kline", {
    "category": "linear",
    "symbol": "BTCUSDT",
    "interval": "30",
    "limit": 131400
})

# Добавляем служебную информацию для ясности
data_to_save = {
    "symbol": "BTCUSDT",
    "interval": "30",
    "fetched_at": datetime.now().isoformat(),
    "data": response  # или response.get('result', {})
}

with open('btc_data_30m.json', 'w', encoding='utf-8') as f:
    json.dump(data_to_save, f, ensure_ascii=False, indent=2)

print("✅ Данные сохранены в btc_data.json")

#api_key=Bg9sqvIb1KXkAOtzN2
#api_secret=Q0unSrZ5ACFhYlPR7xmgQREKnWhG6xl3Ypx9
