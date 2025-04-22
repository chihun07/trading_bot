import sqlite3
import pandas as pd
from upbit_api import get_market_price, get_balance  
from database import setup_database
from config import WALLET_DB, MARKET  # ✅ 수정: `DB_FILE` → `WALLET_DB`
from logger import save_to_wallet_log

def setup_wallet_database():
    """wallet 테이블이 없으면 생성"""
    conn = sqlite3.connect(WALLET_DB)  # ✅ 수정: 기존 DB_FILE → WALLET_DB
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
    print("✅ `wallet` 테이블이 확인되었습니다.")

def display_wallet():
    """보유 자산 평가 금액 출력 및 저장"""
    setup_wallet_database()  # ✅ 테이블이 없으면 생성

    conn = sqlite3.connect(WALLET_DB)  # ✅ 수정
    df = pd.read_sql("SELECT * FROM wallet", conn)
    conn.close()

    if df.empty:
        print("📌 지갑에 보유한 자산이 없습니다.")
        save_to_wallet_log("📌 지갑에 보유한 자산이 없습니다.")
        return

    # ✅ 가격 캐시를 활용하여 API 호출 최소화
    price_cache = {}

    # 평가 금액 계산
    total_assets = 0
    selected_coin_krw = 0
    selected_coin_balance = 0
    selected_coin_price = get_market_price(MARKET)  # ✅ 수정된 `get_market_price()` 사용

    # ✅ 보유 현금(KRW) 정보 가져오기
    krw_balance = df[df["currency"] == "KRW"]["balance"].sum() if "KRW" in df["currency"].values else 0
    total_assets += krw_balance  # ✅ 원화 잔고를 총 자산에 포함

    for index, row in df.iterrows():
        if row["currency"] != "KRW":
            market = f"KRW-{row['currency']}"

            # ✅ 이미 가져온 가격이면 캐시 사용, 없으면 API 호출
            if market not in price_cache:
                price_cache[market] = get_market_price(market)

            price = price_cache[market]
            df.at[index, "current_price"] = int(price) if price else 0
            df.at[index, "krw_value"] = int(float(row["balance"]) * price) if price else 0
            total_assets += df.at[index, "krw_value"]

            if market == MARKET:
                selected_coin_krw = df.at[index, "krw_value"]
                selected_coin_balance = float(row["balance"])

    # 비율 계산
    krw_ratio = (krw_balance / total_assets) * 100 if total_assets > 0 else 0
    selected_coin_ratio = (selected_coin_krw / total_assets) * 100 if total_assets > 0 else 0

    wallet_info = f"""
📊 **자산 비율 분석** 📊
💵 현금(원화) 잔고: {krw_balance:,.0f} 원, 💵 현금(원화) 비율: {krw_ratio:.2f}%, 📈 {MARKET} 비율: {selected_coin_ratio:.2f}%

💰 **{MARKET} 환산 금액** 💰
보유한 {MARKET} 수량: {selected_coin_balance:.6f}, {MARKET} 현재 가격: {selected_coin_price:,.0f} 원,{MARKET} 환산 원화: {selected_coin_krw:,.0f} 원

💳 **총 보유 자산 (KRW 기준)** 💳
총 평가 금액: {total_assets:,.0f} 원
"""

    print(wallet_info)
    save_to_wallet_log(wallet_info)

def save_balance_to_db():
    """현재 보유 중인 자산을 DB에 저장"""
    conn = sqlite3.connect(WALLET_DB)  # ✅ 수정
    cursor = conn.cursor()

    # 업비트 API에서 현재 보유 자산 가져오기
    balances = get_balance()

    if not balances:
        print("⚠️ 보유한 자산이 없습니다.")
        return

    # 기존 데이터 삭제 (항상 최신 데이터 유지)
    cursor.execute("DELETE FROM wallet")

    for asset in balances:
        cursor.execute("""
            INSERT INTO wallet (currency, balance, locked, avg_buy_price, avg_buy_price_modified)
            VALUES (?, ?, ?, ?, ?)
        """, (
            asset["currency"],  
            float(asset["balance"]),  
            float(asset["locked"]),  
            float(asset["avg_buy_price"]) if asset["avg_buy_price"] else 0.0,  
            asset["avg_buy_price_modified"]  
        ))

    conn.commit()
    conn.close()
    print("✅ `wallet` 테이블에 보유 자산이 저장되었습니다.")

if __name__ == "__main__":
    setup_wallet_database()  # ✅ `wallet` 테이블이 없으면 생성
    save_balance_to_db()  # ✅ 보유 자산 저장
    display_wallet()  # ✅ 지갑 정보 표시
