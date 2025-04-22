import sqlite3
from upbit_api import get_market_price
from config import TRADE_HISTORY_DB, MARKET
from logger import save_to_trades_log

def calculate_pnl():
    """손익 계산"""
    conn = sqlite3.connect(TRADE_HISTORY_DB)  # ✅ 개별 DB 사용
    cursor = conn.cursor()

    # ✅ 총 매수 금액 (매수한 모든 내역)
    cursor.execute("""
        SELECT COALESCE(SUM(total_cost), 0) FROM trade_history WHERE market = ? AND trade_type = 'bid'
    """, (MARKET,))
    total_buy_amount = cursor.fetchone()[0]

    # ✅ 총 매도 금액 (매도한 모든 내역)
    cursor.execute("""
        SELECT COALESCE(SUM(total_cost), 0) FROM trade_history WHERE market = ? AND trade_type = 'ask'
    """, (MARKET,))
    total_sell_amount = cursor.fetchone()[0]

    # ✅ 현재 보유한 코인 수량
    cursor.execute("""
        SELECT COALESCE(SUM(volume), 0) FROM trade_history WHERE market = ? AND trade_type = 'bid'
    """, (MARKET,))
    total_bought = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(volume), 0) FROM trade_history WHERE market = ? AND trade_type = 'ask'
    """, (MARKET,))
    total_sold = cursor.fetchone()[0]

    current_balance = total_bought - total_sold  # 현재 보유 코인 수량

    # ✅ 현재 평가 금액
    current_price = get_market_price()
    current_value = current_balance * current_price

    # ✅ 손익 계산
    realized_pnl = total_sell_amount - total_buy_amount  # 실현 손익
    unrealized_pnl = current_value - (total_buy_amount - total_sell_amount)  # 평가 손익
    total_pnl = realized_pnl + unrealized_pnl  # 총 손익

    conn.close()

    # ✅ 로그 저장 및 출력
    pnl_info = f"""
📊 **손익 계산 결과** 📊
💰 총 매수 금액: {total_buy_amount:,.0f} KRW
💰 총 매도 금액: {total_sell_amount:,.0f} KRW
📈 현재 {MARKET} 가격: {current_price:,.0f} KRW
🛒 현재 보유량: {current_balance:.6f} {MARKET.split('-')[1]}
💰 현재 평가 금액: {current_value:,.0f} KRW
✅ 실현 손익: {realized_pnl:,.0f} KRW
📊 평가 손익: {unrealized_pnl:,.0f} KRW
💹 총 손익: {total_pnl:,.0f} KRW
"""

    print(pnl_info)
    save_to_trades_log(pnl_info)  # ✅ 로그 저장
    return total_pnl

if __name__ == "__main__":
    calculate_pnl()
