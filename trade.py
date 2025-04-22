import sqlite3
from upbit_api import get_market_price, get_balance, place_order
from config import TRADE_HISTORY_DB, MARKET

def trade_by_percentage(side, percent):
    """지정된 비율(percent)로 시장가 매수/매도"""
    krw_balance = get_balance("KRW") or 0
    btc_balance = get_balance("BTC") or 0
    current_price = get_market_price() or 0

    if side == "bid":
        order_amount = krw_balance * (percent / 100.0)
        if order_amount < 5000:
            print("⚠️ 최소 주문 금액보다 작음. 주문 취소.")
            return None
        
        # 시장가 매수 => price=주문금액, volume=None
        order_result = place_order(side="bid", price=order_amount, volume=None)
        return order_result  # 성공 시 JSON, 실패면 None

    else:
        # side == "ask"
        sell_volume = round(btc_balance * (percent / 100.0), 8)
        if sell_volume * current_price < 5000:
            print("⚠️ 최소 주문 금액보다 작음. 주문 취소.")
            return None
        
        # 시장가 매도 => price=None, volume=sell_volume
        order_result = place_order(side="ask", price=None, volume=sell_volume)
        return order_result  # 성공 시 JSON, 실패면 None