import os
from config import WALLET_LOG_FILE, TRADES_LOG_FILE

def get_iteration(log_file):
    """현재 몇 번째 실행인지 로그 파일을 확인하여 회차 증가"""
    if not os.path.exists(log_file):
        return 1  # 첫 번째 실행

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        count = sum(1 for line in lines if "회차" in line)  # "회차" 등장 횟수 세기
        return count + 1  # 다음 회차 반환

def save_to_wallet_log(data):
    """회차별 지갑 정보를 log/wallet_log.txt 파일에 추가"""
    iteration = get_iteration(WALLET_LOG_FILE)
    
    with open(WALLET_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{iteration} 회차 (지갑 정보)\n")
        f.write(data)
    
    print(f"✅ {iteration} 회차 지갑 정보가 {WALLET_LOG_FILE} 파일에 저장되었습니다.")

def save_to_trades_log(data):
    """회차별 거래 내역을 log/trades_log.txt 파일에 추가"""
    iteration = get_iteration(TRADES_LOG_FILE)
    
    with open(TRADES_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{iteration} 회차 (거래 내역)\n")
        f.write(data)
    
    print(f"✅ {iteration} 회차 거래 내역이 {TRADES_LOG_FILE} 파일에 저장되었습니다.")
