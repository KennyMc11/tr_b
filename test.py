import hmac
import hashlib
import time
import requests
import os
from dotenv import load_dotenv
from BB import ByBit
import datetime



bybit = ByBit(demo=True)

positions = bybit.get_positions("ETHUSDT")
pos_list = positions.get('result', {}).get('list', [])
if pos_list:
    pos = pos_list[0].get('avgPrice', []) or 0
print(float(pos))


#api_key=Bg9sqvIb1KXkAOtzN2
#api_secret=Q0unSrZ5ACFhYlPR7xmgQREKnWhG6xl3Ypx9
