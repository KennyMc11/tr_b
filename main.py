import hmac
import hashlib
import time
import requests
import os
from dotenv import load_dotenv
from BB import ByBit



bybit = ByBit(demo=True)

def print_balance(balance_response):
    """Красивый вывод баланса"""
    if balance_response.get("retCode") != 0:
        print(f"Ошибка: {balance_response.get('retMsg')}")
        return
    
    accounts = balance_response.get("result", {}).get("list", [])
    
    for account in accounts:
        print(f"\n{'='*50}")
        print(f"Тип счета: {account.get('accountType')}")
        print(f"Общий баланс: {account.get('totalWalletBalance')} USDT")
        print(f"Доступно: {account.get('totalAvailableBalance')} USDT")
        print(f"Эквити: {account.get('totalEquity')} USDT")
        print(f"{'='*50}")
        
        print("\nМонеты:")
        for coin in account.get("coin", []):
            name = coin.get('coin')
            wallet = coin.get('walletBalance')
            usd_value = coin.get('usdValue')
            locked = coin.get('locked')
            available = coin.get('availableToWithdraw')
            
            print(f"  {name}:")
            print(f"    Баланс: {wallet} ({usd_value} USD)")
            print(f"    Доступно: {available}")
            print(f"    Заблокировано: {locked}")


price = bybit.get_current_price("BTCUSDT")
current_price = float(price['result']['list'][0]['lastPrice'])
print(f"Текущая цена: {current_price}")


"""order = bybit.place_order(
    symbol="BTCUSDT",
    side="Sell",
    order_type="Market",
    qty=0.001
)
print("Покупка с SL/TP:", order)"""

"""# 4. Продажа
order = bybit.place_order(
    symbol="BTCUSDT",
    side="Buy",
    order_type="Market",
    qty=0.002
)
print("Рыночная продажа:", order)"""

# 6. Получение открытых ордеров
#open_orders = bybit.get_open_orders("BTCUSDT")
#positions = bybit.get_positions("BTCUSDT")
#print("Открытые ордера:", open_orders)
#print("Позиции:", positions)

st240 = bybit.get_supertrend("BTCUSDT", "240", 15, 3.0)
print(f"\nSuperTrend {st240['symbol']}, интервал: {st240["interval"]} мин, период: {st240["period"]} свечей * 5")
print(f"Текущий сигнал: {st240['current_signal']}")
print(f"SuperTrend: {st240['current_supertrend']}")
print(f"Цена: {st240['current_price']}")
print(f"Смена тренда: {st240['trend_change']}")
print(f"Количество свечей: {st240['candles_count']}\n")


candles_for_atr = bybit.get_supertrend("BTCUSDT", "60", 15, 3.0)
#print(f"ATR 48 часовых свеч: {candles_for_atr['candles'][0]['atr'][-45:]}")
atr = candles_for_atr['candles'][0]['atr'][-45:]
mean_atr = bybit.weighted_mean(atr)
print(f"Среднее взвешенное {candles_for_atr['symbol']} ATR за 48 часов: {mean_atr}\n")
