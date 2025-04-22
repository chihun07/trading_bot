import os
import sqlite3
import pandas as pd
from upbit_api import get_trade_history
from config import TRANSACTIONS_DB, LOG_DIR, MARKET, TRADES_LOG_FILE

def setup_transactions_database():
    """transactions 테이블이 없으면 생성"""
    conn = sqlite3.connect(TRANSACTIONS_DB)  # ✅ DB 변경
    cursor = conn.cursor()

    # ✅ 거래 내역을 저장할 transactions 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_time TEXT,
            market TEXT,
            price REAL,
            volume REAL,
            trade_type TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ 데이터베이스 초기화 완료 ({TRANSACTIONS_DB})")

def save_to_database(trades, market):
    """거래 내역을 transactions.db에 저장"""
    conn = sqlite3.connect(TRANSACTIONS_DB)  # ✅ DB 변경
    cursor = conn.cursor()

    for trade in trades:
        cursor.execute("""
            INSERT INTO transactions (trade_time, market, price, volume, trade_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            trade["trade_date_utc"] + " " + trade["trade_time_utc"],
            market,
            float(trade["trade_price"]),
            float(trade["trade_volume"]),
            trade["ask_bid"]
        ))

    conn.commit()
    conn.close()
    print(f"✅ 거래 내역이 {TRANSACTIONS_DB}에 저장되었습니다.")

def save_to_trades_log(data):
    """거래 내역을 `log/trades_log.txt`에 덮어쓰기"""
    with open(TRADES_LOG_FILE, "w", encoding="utf-8") as f:
        f.write("📊 **최근 거래 내역** 📊\n\n")
        f.write(data)

    print(f"✅ 거래 내역이 {TRADES_LOG_FILE} 파일에 저장되었습니다.")

def display_buy_sell_data():
    """매수(BID) 및 매도(ASK) 내역을 나눠서 출력 및 저장"""
    setup_transactions_database()  # ✅ 테이블이 없으면 생성

    conn = sqlite3.connect(TRANSACTIONS_DB)  # ✅ DB 변경
    df = pd.read_sql("SELECT * FROM transactions", conn)
    conn.close()

    if df.empty:
        print("📌 거래 내역이 없습니다.")
        save_to_trades_log("📌 거래 내역이 없습니다.")
        return

    # 매수(BID) 및 매도(ASK) 데이터 분리
    buy_df = df[df["trade_type"].str.lower() == "bid"]
    sell_df = df[df["trade_type"].str.lower() == "ask"]

    output = "\n📊 **매수 거래 내역** 📊\n"
    output += buy_df.tail(10).to_string(index=False) + "\n"

    output += "\n📊 **매도 거래 내역** 📊\n"
    output += sell_df.tail(10).to_string(index=False) + "\n"

    save_to_trades_log(output)

    print("✅ 거래 내역이 저장되었습니다.")

if __name__ == "__main__":
    setup_transactions_database()
    display_buy_sell_data()
