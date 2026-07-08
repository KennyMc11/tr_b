import hmac
import hashlib
import time
import requests
import os
from dotenv import load_dotenv
from BB import ByBit
import datetime



bybit = ByBit(demo=True)

time_now = datetime.datetime.now()

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


"""price = bybit.get_current_price("BTCUSDT")
current_price = float(price['result']['list'][0]['lastPrice'])
print(f"Текущая цена: {current_price}")"""

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
print(f"\nSuperTrend {st240['symbol']}, интервал: {st240["interval"]} мин, период: {st240["period"]} свечей * 3")
print(f"Текущий сигнал: {st240['current_signal']}")
print(f"SuperTrend: {st240['current_supertrend']}")
print(f"Цена: {st240['current_price']}")
print(f"Смена тренда: {st240['trend_change']}")
print(f"Количество свечей: {st240['candles_count']}\n")


atr_data_60 = bybit.get_atr_from_kline("BTCUSDT", interval="60", period=15)
atr_data_240 = bybit.get_atr_from_kline("BTCUSDT", interval="240", period=15)


print(f"📊 Текущий ATR 60 мин: {atr_data_60['current_atr']} пунктов")
print(f"📊 ATR в % от цены: {atr_data_60['current_atr_percent']}%")
print(f"📊 Текущая цена: {atr_data_60['current_price']}\n")

print(f"📊 Текущий ATR 240 мин: {atr_data_240['current_atr']} пунктов")
print(f"📊 ATR в % от цены: {atr_data_240['current_atr_percent']}%")
print(f"📊 Текущая цена: {atr_data_240['current_price']}\n")


positions = bybit.get_positions("BTCUSDT")
print(positions['result']['list'][0]["avgPrice"])

def order(symbol):
    try:
        # Проверяем, есть ли уже открытая позиция
        positions = bybit.get_positions(symbol)
        if float(positions['result']['list'][0]["avgPrice"]) > 0:
            print(f"⏸️ Уже есть открытая позиция: {symbol} цена входа {positions['result']['list'][0]["avgPrice"]}")
            return

        price = bybit.get_current_price(symbol)
        current_price = float(price['result']['list'][0]['lastPrice'])

        st_240 = bybit.get_supertrend(symbol, "240", 15, 3.0)
        st_15 = bybit.get_supertrend(symbol, "15", 15, 3.0)

        atr_data30 = bybit.get_atr_from_kline(symbol, interval="30", period=15)
        atr_30 = atr_data30['current_atr']

        atr_data60 = bybit.get_atr_from_kline(symbol, interval="60", period=15)
        atr_60 = atr_data60['current_atr']

        bybit.set_margin_mode("ISOLATED_MARGIN")
        print("Изолированная маржа")
        bybit.set_leverage(symbol, 25)
        print("Плечо: x25")

        if st_240['current_signal'] == "LONG" and st_15['current_signal'] == "SHORT" and abs(current_price - st_240['current_supertrend'])>= atr_60:
            stop = current_price - (atr_30 * 2)
            take = current_price + (atr_30 * 5)
            bybit.place_order(
                symbol=symbol,
                side="Buy",
                order_type="Market",
                qty=0.01,
                stop_loss=stop,
                take_profit=take
                )
            print(f"Покупка {symbol}\nЦена: {current_price}\nSL={stop}\nTP={take}\n{time_now}")

        elif st_240['current_signal'] == "SHORT" and st_15['current_signal'] == "LONG" and abs(current_price - st_240['current_supertrend'])>= atr_60:
            stop = current_price + (atr_30 * 2)
            take = current_price - (atr_30 * 5)
            bybit.place_order(
                symbol=symbol,
                side="Sell",
                order_type="Market",
                qty=0.01,
                stop_loss=stop,
                take_profit=take
                )
            print(f"Продажа {symbol}\nЦена: {current_price}\nSL={stop}\nTP={take}\n{time_now}")
        else:
            print("Нейтральный тренд или далеко от линии поддержки/сопротивления")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    while True:
        order("BTCUSDT")
        time.sleep(900)  # 900 секунд = 15 минут