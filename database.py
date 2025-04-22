import sqlite3
from upbit_api import get_balance
from config import TRANSACTIONS_DB, TRADE_HISTORY_DB, WALLET_DB, TRADE_STATE_DB

### ✅ 1. 개별 데이터베이스 초기화 (거래 내역, 지갑 정보, 손익 계산, 자동매매 상태)
def setup_database():
    """각 테이블을 별도의 데이터베이스 파일로 분리하여 초기화"""

    # ✅ 거래 내역 DB 초기화
    conn = sqlite3.connect(TRANSACTIONS_DB)
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
    print(f"✅ `{TRANSACTIONS_DB}` 초기화 완료 (transactions 테이블 생성됨)")

    # ✅ 손익 계산을 위한 거래 기록 DB 초기화
    conn = sqlite3.connect(TRADE_HISTORY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_time TEXT,
            market TEXT,
            trade_type TEXT,
            price REAL,
            volume REAL,
            total_cost REAL
        )
    """)
    conn.commit()
    conn.close()
    print(f"✅ `{TRADE_HISTORY_DB}` 초기화 완료 (trade_history 테이블 생성됨)")

    # ✅ 보유 자산 DB 초기화
    conn = sqlite3.connect(WALLET_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallet (
            currency TEXT PRIMARY KEY,
            balance REAL,
            locked REAL,
            avg_buy_price REAL,
            avg_buy_price_modified BOOLEAN
        )
    """)
    conn.commit()
    conn.close()
    print(f"✅ `{WALLET_DB}` 초기화 완료 (wallet 테이블 생성됨)")

    # ✅ 자동매매 상태 저장 DB 초기화
    setup_trade_state_db()  # ✅ trade_state.db 테이블 생성

### ✅ 2. 자동매매 상태 저장을 위한 DB (`trade_state.db`) 초기화
def setup_trade_state_db():
    """자동매매 상태를 저장하는 trade_state 테이블을 생성"""
    conn = sqlite3.connect(TRADE_STATE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_buy_price REAL DEFAULT 0,
            last_sell_time REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    print(f"✅ `{TRADE_STATE_DB}` 초기화 완료 (trade_state 테이블 생성됨)")

### ✅ 3. 현재 보유 자산을 `wallet.db`에 저장
def save_balance_to_db():
    """현재 보유 중인 자산을 wallet.db에 저장"""
    conn = sqlite3.connect(WALLET_DB)
    cursor = conn.cursor()

    # ✅ 업비트 API에서 현재 보유 자산 가져오기
    balances = get_balance()

    if not balances:
        print("⚠️ 보유한 자산이 없습니다.")
        return

    # ✅ 기존 데이터 삭제 (항상 최신 데이터 유지)
    cursor.execute("DELETE FROM wallet")

    for asset in balances:
        cursor.execute("""
            INSERT INTO wallet (currency, balance, locked, avg_buy_price, avg_buy_price_modified)
            VALUES (?, ?, ?, ?, ?)
        """, (
            asset["currency"],  # 화폐 종류 (예: KRW, BTC, ETH)
            float(asset["balance"]),  # 보유 수량
            float(asset["locked"]),  # 주문 대기 중 수량
            float(asset["avg_buy_price"]) if asset["avg_buy_price"] else 0.0,  # 평균 매수가
            asset["avg_buy_price_modified"]  # 매수가 변경 여부
        ))

    conn.commit()
    conn.close()
    print(f"✅ `{WALLET_DB}`에 보유 자산이 저장되었습니다.")

### ✅ 4. `last_buy_price` 저장 및 불러오기
def save_last_buy_price(price):
    """매수가를 trade_state.db에 저장"""
    conn = sqlite3.connect(TRADE_STATE_DB)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM trade_state")  # 기존 데이터 삭제
    cursor.execute("INSERT INTO trade_state (last_buy_price, last_sell_time) VALUES (?, ?)", (price, load_last_sell_time()))
    
    conn.commit()
    conn.close()
    print(f"💾 매수가 {price:,.0f} 원 저장 완료")

def load_last_buy_price():
    """저장된 매수가를 trade_state.db에서 불러오기"""
    setup_trade_state_db()  # ✅ 테이블이 없으면 생성
    conn = sqlite3.connect(TRADE_STATE_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT last_buy_price FROM trade_state ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()

    conn.close()
    return result[0] if result and result[0] is not None else 0  # 저장된 값이 없으면 0 반환

### ✅ 5. `last_sell_time` 저장 및 불러오기
def save_last_sell_time(time_value):
    """마지막 매도 시간을 trade_state.db에 저장"""
    conn = sqlite3.connect(TRADE_STATE_DB)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM trade_state")  # 기존 데이터 삭제
    cursor.execute("INSERT INTO trade_state (last_buy_price, last_sell_time) VALUES (?, ?)", (load_last_buy_price(), time_value))
    
    conn.commit()
    conn.close()
    print(f"💾 마지막 매도 시간 저장 완료: {time_value}")

def load_last_sell_time():
    """저장된 마지막 매도 시간을 trade_state.db에서 불러오기"""
    setup_trade_state_db()  # ✅ 테이블이 없으면 생성
    conn = sqlite3.connect(TRADE_STATE_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT last_sell_time FROM trade_state ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()

    conn.close()
    return result[0] if result and result[0] is not None else 0  # 저장된 값이 없으면 0 반환

### ✅ 6. 데이터베이스 설정 실행
if __name__ == "__main__":
    setup_database()  # ✅ 개별 데이터베이스 파일 생성
    save_balance_to_db()  # ✅ 지갑 정보 저장
