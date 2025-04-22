from wallet import display_wallet
from trades import display_buy_sell_data
from database import setup_database
from auto_trade import auto_trade 
from calculate_pnl import calculate_pnl

def main():
    """전체 프로그램 실행"""
    setup_database()

    print("🚀 지갑 정보를 조회하는 중...")
    display_wallet()

    print("🚀 거래 내역을 조회하는 중...")
    display_buy_sell_data()

    """자동 매매 실행"""
    try:
        auto_trade()  # ✅ 자동 매매 시작
    except KeyboardInterrupt:
        print("\n🚀 프로그램 종료 중... 손익 정리")
        calculate_pnl()  # ✅ 종료 시 손익 계산
        print("✅ 프로그램 종료 완료.")

if __name__ == "__main__":
    main()
