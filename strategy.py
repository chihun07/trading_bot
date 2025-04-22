import requests
from upbit_api import get_current_price
from config import MARKET, SERVER_URL

def get_moving_averages(short_window=5, long_window=20):
    """이동 평균선 계산"""
    url = f"{SERVER_URL}/v1/candles/days"
    params = {"market": MARKET, "count": long_window}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        prices = [candle["trade_price"] for candle in response.json()]
        short_ma = sum(prices[:short_window]) / short_window
        long_ma = sum(prices) / long_window
        return short_ma, long_ma
    return None, None

def decide_trade():
    """매매 전략 결정"""
    short_ma, long_ma = get_moving_averages()
    
    if short_ma and long_ma:
        if short_ma > long_ma:
            return "BUY"
        elif short_ma < long_ma:
            return "SELL"
    return "HOLD"
