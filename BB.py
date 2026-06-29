import hmac
import hashlib
import time
import requests
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


load_dotenv()

class ByBit:
    def __init__(self, api_key="", api_secret="", testnet=True):
        self.api_key = os.getenv('api_key')
        self.api_secret = ('api_secret')
        self.base = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
    
    def _sign(self, params, timestamp, recv_window):
        # recv_window добавляется как значение после ключа, без названия параметра!
        param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign_str = f"{timestamp}{self.api_key}{recv_window}{param_str}"
        print(f"Sign string: {sign_str}")
        return hmac.new(
            self.api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _req(self, method, path, params=None, auth=False):
        url = f"{self.base}/v5{path}"
        headers = {"Content-Type": "application/json"}
        
        if auth:
            timestamp = str(int(time.time() * 1000))
            recv_window = "5000"
            params = params or {}
            
            headers.update({
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-SIGN": self._sign(params, timestamp, recv_window),
                "X-BAPI-RECV-WINDOW": recv_window
            })
        
        if method == "GET":
            r = requests.get(url, params=params, headers=headers, timeout=30)
        else:
            r = requests.post(url, json=params, headers=headers, timeout=30)
        
        return r.json()
    
    def get_current_price(self, symbol: str, category: str = "linear") -> Optional[float]:
        """
        Получение текущей цены фьючерса
        """
        try:
            response = self._req("GET", "/market/tickers", {
                "category": category,
                "symbol": symbol
            })
            
            return response
            
        except Exception as e:
            print(f"Exception in get_current_price: {e}")
            return None

    def get_supertrend(self, symbol: str, interval: str = "60", period: int = 15, multiplier: float = 3.0, category: str = "linear"):
        # Получаем свечи
        response = self._req("GET", "/market/kline", {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": period * 5
        })
        
        if response.get("retCode") != 0:
            return {"error": response.get("retMsg")}
        
        data = response.get("result", {}).get("list", [])
        
        # Просто возвращаем свечи
        return {
            "candles": data,
            "period": period,
            "multiplier": multiplier
        }
    


# Пример
bybit = ByBit(testnet=True)
data = bybit.get_current_price("BTCUSDT")
st = bybit.get_supertrend("BTCUSDT")
print(data['result']['list'][0]['indexPrice'])
print(st)