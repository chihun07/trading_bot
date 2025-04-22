import sqlite3
import pandas as pd
from config import TRANSACTIONS_DB

def setup_transactions_database():
    """transactions 테이블이 없으면 생성"""
    conn = sqlite3.connect(TRANSACTIONS_DB)  # ✅ 변경
    cursor = conn.cursor()

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
    print("✅ `transactions` 테이블이 확인되었습니다.")

def save_transaction(trade_time, market, price, volume, trade_type):
    """거래 내역을 transactions 테이블에 저장"""
    setup_transactions_database()  # ✅ 테이블이 없으면 생성

    conn = sqlite3.connect(TRANSACTIONS_DB)  # ✅ 변경
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions (trade_time, market, price, volume, trade_type)
        VALUES (?, ?, ?, ?, ?)
    """, (trade_time, market, price, volume, trade_type))

    conn.commit()
    conn.close()
    print("✅ 거래 내역이 transactions 테이블에 저장되었습니다.")

if __name__ == "__main__":
    setup_transactions_database()
