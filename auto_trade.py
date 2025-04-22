import time
import pandas as pd
from trade import trade_by_percentage
from upbit_api import (
    get_market_price,
    get_ohlcv,
    calculate_rsi,
    calculate_moving_average,
    calculate_volatility_breakout,
    get_balance
)
from config import MARKET
from calculate_pnl import calculate_pnl
from wallet import display_wallet, save_balance_to_db
from database import load_last_buy_price, save_last_buy_price, load_last_sell_time, save_last_sell_time

COOLDOWN_PERIOD = 300  # 5분 동안 추가 거래 제한
PRINT_INTERVAL = 100    # 100초마다만 상태 출력

# ✅ 저장된 매수/매도 관련 데이터 불러오기
last_buy_time = 0
last_sell_time = load_last_sell_time()  # ✅ 마지막 매도 시간을 DB에서 불러오기
last_print_time = 0  # 마지막으로 프린트한 시각

# ✅ 저장된 매수가 불러오기 (없으면 현재 가격으로 설정)
last_buy_price = load_last_buy_price()
print(f"📌 기존 매수가 설정됨: {last_buy_price:,.0f} KRW")
if last_buy_price == 0 or last_buy_price is None:
    last_buy_price = get_market_price(MARKET) or 0  # 현재 가격을 가져오고, 실패하면 0
    save_last_buy_price(last_buy_price)  # DB에 저장
    print(f"📌 초기 매수가 설정됨: {last_buy_price:,.0f} KRW")

def auto_trade():
    global last_buy_time, last_sell_time, last_print_time, last_buy_price

    print("🚀 자동 매매를 시작합니다...")

    while True:
        current_time = time.time()

        # ✅ 1. OHLCV 데이터 불러오기
        ohlcv = get_ohlcv(MARKET, 200)
        if not isinstance(ohlcv, list) or len(ohlcv) == 0:
            print("⚠️ OHLCV 데이터를 가져오지 못했습니다. 10초 후 재시도...")
            time.sleep(10)
            continue

        ohlcv_df = pd.DataFrame(ohlcv)
        if "trade_price" not in ohlcv_df.columns:
            print("⚠️ 'trade_price' 컬럼이 없습니다. API 응답을 확인하세요.")
            time.sleep(10)
            continue

        # ✅ 2. 각종 지표 계산
        close_prices = ohlcv_df["trade_price"]
        current_price = get_market_price(MARKET)
        rsi = calculate_rsi(close_prices)
        short_ma, long_ma = calculate_moving_average(ohlcv_df, 5, 20)
        breakout_price = calculate_volatility_breakout(ohlcv_df)

        # ✅ 3. 보유 잔고 확인 (에러 방지)
        krw_balance = get_balance("KRW") or 0
        btc_balance = get_balance("BTC") or 0

        # ✅ 4. 현재 평가 금액 계산
        total_asset_value = krw_balance + (btc_balance * current_price)

        # ✅ 100초마다 상태 정보 출력
        if current_time - last_print_time >= PRINT_INTERVAL:
            print(f"\n📈 현재 {MARKET} 가격: {current_price:,.0f} KRW")
            print(f"📊 RSI: {rsi:.2f}, 단기MA: {short_ma:,.0f}, 장기MA: {long_ma:,.0f}, 돌파가: {breakout_price:,.0f}")
            print(f"💰 KRW 잔액: {krw_balance:,.0f} | BTC 잔액: {btc_balance} | 총 평가: {total_asset_value:,.0f} KRW")
            last_print_time = current_time

        ############################################
        # ✅ 매수 로직
        ############################################
        if (
            (rsi < 30 or short_ma > long_ma)
            and (current_time - last_buy_time > COOLDOWN_PERIOD)
            and btc_balance == 0
            and krw_balance > 5000
        ):
            if rsi < 30:
                print("📉 [매수] RSI 과매도 감지")
            else:
                print("📉 [매수] 골든크로스 감지")

            # ✅ 매수가 기록 (손익 분석 활용)
            order_result = trade_by_percentage(side="bid", percent=90)
            if order_result is not None:
                last_buy_time = current_time
                last_buy_price = current_price  # ✅ 매수가 저장
                save_last_buy_price(last_buy_price)  # ✅ DB에 저장
                print(f"✅ 매수 주문 완료! 저장된 매수가: {last_buy_price:,.0f} KRW")
                display_wallet()
                save_balance_to_db()
            else:
                print("⚠️ 매수 주문이 실패하여 후속 처리하지 않습니다.")

        ############################################
        # ✅ 매도 로직
        ############################################
        if (
            (rsi > 70 or current_price > breakout_price or current_price > last_buy_price * 1.01)
            and (current_price > last_buy_price * 1.005 or current_price > last_buy_price * 1.01)
            and (current_time - last_sell_time > COOLDOWN_PERIOD)
            and btc_balance > 0
        ):
            # ✅ 매도 사유 출력
            if rsi > 70:
                print("📈 [매도] RSI 과매수 감지")
            elif current_price > breakout_price:
                print("📈 [매도] 변동성 돌파 초과 감지")
            elif current_price > last_buy_price * 1.01:
                print("📈 [매도] 1% 상승 감지 (매도 실행)")
            elif current_price > last_buy_price * 1.005:
                print("📈 [매도] 0.5% 상승 감지 (매도 실행)")

            # ✅ 매도 주문 실행
            order_result = trade_by_percentage(side="ask", percent=100)
            if order_result is not None:
                last_sell_time = current_time
                save_last_sell_time(last_sell_time)  # ✅ 매도 시간 저장
                print("✅ 매도 주문이 성공적으로 실행되었습니다.")

                # ✅ 손익 계산 및 업데이트
                calculate_pnl()
                display_wallet()
                save_balance_to_db()
            else:
                print("⚠️ 매도 주문이 실패하여 후속 처리하지 않습니다.")

        else:
            # ✅ 매도가 불발된 경우, 남은 쿨다운이 있으면 안내
            if (current_time - last_sell_time) <= COOLDOWN_PERIOD:
                remaining_time = int(COOLDOWN_PERIOD - (current_time - last_sell_time))
                print(f"⏳ 매도 대기 중... (쿨다운 {remaining_time}초 남음)")

        # ✅ 10초 후 반복 실행
        time.sleep(10)

if __name__ == "__main__":
    auto_trade()
