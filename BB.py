import hmac
import hashlib
import time
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

class ByBit:
    def __init__(self, api_key="", api_secret="", demo=True):
        self.demo = demo
        self.api_key_demo = "Bg9sqvIb1KXkAOtzN2"
        self.api_secret_demo = "Q0unSrZ5ACFhYlPR7xmgQREKnWhG6xl3Ypx9"
        
        # Выбор endpoint
        if demo:
            self.api_key = self.api_key_demo
            self.api_secret = self.api_secret_demo
            self.base = "https://api-demo.bybit.com"
            print("ДЕМО РЕЖИМ")
        else:
            self.api_key = api_key or os.getenv('api_key')
            self.api_secret = api_secret or os.getenv('api_secret')
            self.base = "https://api.bybit.com"
            print("РАЛЬНЫЙ РЕЖИМ")
    
    def _sign(self, params, timestamp, recv_window, method="GET"):
        if method == "GET" and params:
            sorted_params = dict(sorted(params.items()))
            param_str = "&".join([f"{k}={v}" for k, v in sorted_params.items()])
            sign_str = f"{timestamp}{self.api_key}{recv_window}{param_str}"
        else:
            # Для POST - сортируем параметры
            if params:
                # Сортируем по ключам
                sorted_params = dict(sorted(params.items()))
                param_str = json.dumps(sorted_params)
            else:
                param_str = "{}"
            sign_str = f"{timestamp}{self.api_key}{recv_window}{param_str}"
        
        print(f"🔑 Строка для подписи: {sign_str}")
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"✅ Подпись: {signature}")
        return signature
    
    def _req(self, method, path, params=None, auth=False):
        url = f"{self.base}{path}"
        headers = {"Content-Type": "application/json"}
        
        if auth:
            timestamp = str(int(time.time() * 1000))
            recv_window = "5000"
            params = params or {}
            params = {k: v for k, v in params.items() if v is not None}
            # Сортируем перед подписью
            params = dict(sorted(params.items()))
            
            signature = self._sign(params, timestamp, recv_window, method)
            
            headers.update({
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-SIGN": signature,
                "X-BAPI-RECV-WINDOW": recv_window
            })
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=30)
            else:
                response = requests.post(url, json=params, headers=headers, timeout=30)
            
            #print(f"📡 URL: {url}")
            #print(f"📡 Статус: {response.status_code}")
            #print(f"📄 Ответ: {response.text[:500]}")
            
            if response.status_code != 200:
                return {"retCode": response.status_code, "retMsg": response.text}
            
            return response.json()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    def get_current_price(self, symbol: str, category: str = "linear"):
        response = self._req("GET", "/v5/market/tickers", {
            "category": category,
            "symbol": symbol
        })
        return response
    
    def _calculate_atr(self, highs, lows, closes, period):
        """Расчет Average True Range"""
        tr_values = []
        
        # Первое значение True Range
        tr_values.append(highs[0] - lows[0])
        
        # Расчет True Range для остальных значений
        for i in range(1, len(highs)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr)
        
        # Расчет ATR (используем RMA - скользящее среднее по Уайлдеру)
        atr_values = []
        
        for i in range(len(tr_values)):
            if i == 0:
                atr_values.append(tr_values[0])
            elif i < period:
                atr_values.append(sum(tr_values[:i+1]) / (i+1))
            else:
                atr_values.append((atr_values[i-1] * (period - 1) + tr_values[i]) / period)
        
        return atr_values
    
    def _calculate_supertrend(self, highs, lows, closes, period, multiplier):
        """Расчет индикатора SuperTrend"""
        if len(highs) < period:
            return []
        
        # Расчет ATR
        atr = self._calculate_atr(highs, lows, closes, period)
        
        # Базовый расчет верхней и нижней полосы
        upper_band = []
        lower_band = []
        
        for i in range(len(highs)):
            hl2 = (highs[i] + lows[i]) / 2
            upper_band.append(hl2 + multiplier * atr[i])
            lower_band.append(hl2 - multiplier * atr[i])
        
        # Финальный расчет с учетом тренда
        final_upper = [0] * len(highs)
        final_lower = [0] * len(highs)
        
        for i in range(len(highs)):
            if i == 0:
                final_upper[i] = upper_band[i]
                final_lower[i] = lower_band[i]
            else:
                if closes[i-1] > final_upper[i-1]:
                    final_lower[i] = max(lower_band[i], final_lower[i-1])
                else:
                    final_lower[i] = lower_band[i]
                    
                if closes[i-1] < final_lower[i-1]:
                    final_upper[i] = min(upper_band[i], final_upper[i-1])
                else:
                    final_upper[i] = upper_band[i]
        
        # Определение сигнала и значения SuperTrend
        result = []
        for i in range(len(highs)):
            if closes[i] > final_lower[i]:
                signal = "LONG"
                supertrend_value = final_lower[i]
            elif closes[i] < final_upper[i]:
                signal = "SHORT"
                supertrend_value = final_upper[i]
            else:
                # Если не определено, используем предыдущее значение
                if i > 0:
                    signal = result[i-1]["signal"]
                    supertrend_value = final_lower[i] if signal == "LONG" else final_upper[i]
                else:
                    signal = "NEUTRAL"
                    supertrend_value = final_lower[i]
            
            result.append({
                "supertrend": round(supertrend_value, 4),
                "signal": signal,
                "upper_band": round(final_upper[i], 4),
                "lower_band": round(final_lower[i], 4),
                "atr": atr
            })
        
        return result
    
    def get_supertrend(self, symbol: str, interval: str = "60", period: int = 15, 
                       multiplier: float = 3.0, category: str = "linear"):
        """
        Получение и расчет индикатора SuperTrend
        
        Args:
            symbol: Торговая пара (например, "BTCUSDT")
            interval: Интервал свечей ("1", "5", "15", "30", "60", "240", "D", "W", "M")
            period: Период для расчета ATR (по умолчанию 15)
            multiplier: Множитель для ATR (по умолчанию 3.0)
            category: Категория ("linear", "spot", "inverse")
        
        Returns:
            dict с результатами расчета
        """
        # Запрашиваем больше свечей для точного расчета
        response = self._req("GET", "/v5/market/kline", {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": period * 5
        })
        
        if response.get("retCode") != 0:
            return {"error": response.get("retMsg")}
        
        data = response.get("result", {}).get("list", [])
        
        if len(data) < period:
            return {"error": f"Недостаточно данных. Получено {len(data)}, требуется минимум {period}"}
        
        # Данные приходят в обратном порядке (от новых к старым)
        data.reverse()
        
        # Извлекаем цены из свечей
        timestamps = [candle[0] for candle in data]
        opens = [float(candle[1]) for candle in data]
        highs = [float(candle[2]) for candle in data]
        lows = [float(candle[3]) for candle in data]
        closes = [float(candle[4]) for candle in data]
        volumes = [float(candle[5]) for candle in data]
        
        # Рассчитываем SuperTrend
        supertrend_data = self._calculate_supertrend(highs, lows, closes, period, multiplier)
        
        if not supertrend_data:
            return {"error": "Ошибка расчета SuperTrend"}
        
        # Формируем результат с полной информацией о свечах
        candles_result = []
        for i in range(len(data)):
            candles_result.append({
                "timestamp": timestamps[i],
                "open": opens[i],
                "high": highs[i],
                "low": lows[i],
                "close": closes[i],
                "volume": volumes[i],
                "supertrend": supertrend_data[i]["supertrend"],
                "signal": supertrend_data[i]["signal"],
                "upper_band": supertrend_data[i]["upper_band"],
                "lower_band": supertrend_data[i]["lower_band"],
                "atr": supertrend_data[i]["atr"]
            })
        
        # Определяем последние сигналы для удобства
        current = candles_result[-1]
        previous = candles_result[-2] if len(candles_result) > 1 else None
        
        # Проверяем смену тренда
        trend_change = False
        if previous and current["signal"] != previous["signal"]:
            trend_change = True
        
        return {
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "multiplier": multiplier,
            "current_signal": current["signal"],
            "current_supertrend": current["supertrend"],
            "current_price": current["close"],
            "trend_change": trend_change,
            "previous_signal": previous["signal"] if previous else None,
            "candles_count": len(candles_result),
            "candles": candles_result
        }

    def get_supertrend_signal(self, symbol: str, interval: str = "60", period: int = 15, 
                              multiplier: float = 3.0, category: str = "linear"):
        """
        Получение только текущего сигнала SuperTrend
        
        Returns:
            dict с текущим сигналом
        """
        result = self.get_supertrend(symbol, interval, period, multiplier, category)
        
        if "error" in result:
            return result
        
        return {
            "symbol": symbol,
            "interval": interval,
            "signal": result["current_signal"],
            "supertrend": result["current_supertrend"],
            "price": result["current_price"],
            "trend_change": result["trend_change"]
        }
    
    
    def get_balance(self, account_type: str = "UNIFIED"):
        """
        Получение баланса
        
        Args:
            account_type: Тип счета - "UNIFIED" (универсальный), "SPOT" (спот), "CONTRACT" (фьючерсы)
        """
        response = self._req("GET", "/v5/account/wallet-balance", {
            "accountType": account_type
        }, auth=True)
        
        return response

    def place_order(self, symbol: str, side: str, order_type: str, qty: float, 
                    price: float = None, category: str = "linear"):
        """
        Размещение ордера (без SL/TP)
        """
        params = {
            "category": category,
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(qty),
            "timeInForce": "GTC"
        }
        
        if order_type == "Limit" and price:
            params["price"] = str(price)
        
        response = self._req("POST", "/v5/order/create", params, auth=True)
        return response


    def set_stop_loss(self, symbol: str, side: str, stop_loss: float, 
                    qty: float = None, category: str = "linear",
                    position_idx: int = 0):
        """Установка стоп-лосса"""
        params = {
            "category": category,
            "symbol": symbol,
            "side": side,
            "orderType": "Market",
            "stopLoss": str(stop_loss),
            "positionIdx": position_idx,
            "timeInForce": "GTC"
        }
        if qty:
            params["qty"] = str(qty)
        
        response = self._req("POST", "/v5/order/create", params, auth=True)
        return response

    def set_take_profit(self, symbol: str, side: str, take_profit: float, 
                        qty: float = None, category: str = "linear",
                        position_idx: int = 0):
        """Установка тейк-профита"""
        params = {
            "category": category,
            "symbol": symbol,
            "side": side,
            "orderType": "Market",
            "takeProfit": str(take_profit),
            "positionIdx": position_idx,
            "timeInForce": "GTC"
        }
        if qty:
            params["qty"] = str(qty)
        
        response = self._req("POST", "/v5/order/create", params, auth=True)
        return response


    def cancel_order(self, symbol: str, order_id: str, category: str = "linear"):
        """Отмена ордера"""
        response = self._req("POST", "/v5/order/cancel", {
            "category": category,
            "symbol": symbol,
            "orderId": order_id
        }, auth=True)
        return response


    def get_open_orders(self, symbol: str = None, category: str = "linear"):
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol
        
        response = self._req("GET", "/v5/order/realtime", params, auth=True)
        return response

    def get_positions(self, symbol: str = None, category: str = "linear"):
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol
        
        response = self._req("GET", "/v5/position/list", params, auth=True)
        return response

    def weighted_mean(self, data, min_weight=0.1, max_weight=1.0):
        """
        Вычисляет взвешенное среднее с плавно возрастающими весами.
        Args:
            data: список чисел
            min_weight: вес первого элемента (по умолчанию 0.1)
            max_weight: вес последнего элемента (по умолчанию 1.0)
        Returns:
            взвешенное среднее
        """
        n = len(data)
        
        if n == 0:
            return 0
        
        # Создаем веса от min_weight до max_weight равномерно
        if n == 1:
            weights = [1.0]  # если один элемент, вес = 1
        else:
            weights = [min_weight + (max_weight - min_weight) * i / (n - 1) for i in range(n)]
        
        # Считаем взвешенное среднее
        weighted_mean = sum(d * w for d, w in zip(data, weights)) / sum(weights)
        
        return weighted_mean


"""bybit = ByBit(demo=True)
x = bybit.get_balance()
print(x)"""