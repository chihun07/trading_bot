import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 업비트 API 키 설정
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")
SERVER_URL = "https://api.upbit.com"

# 저장할 폴더 경로 설정
DB_DIR = "data"  # 데이터베이스 폴더
LOG_DIR = "log"  # 로그 폴더

# ✅ 데이터베이스 파일 개별 저장
WALLET_DB = os.path.join(DB_DIR, "wallet.db")  # ✅ 지갑 정보 전용 DB
TRADE_HISTORY_DB = os.path.join(DB_DIR, "trade_history.db")  # ✅ 거래 기록 DB
TRANSACTIONS_DB = os.path.join(DB_DIR, "transactions.db")  # ✅ 거래 내역 DB
TRADE_STATE_DB = os.path.join(DB_DIR, "trade_state.db")  # ✅ 자동매매 상태 저장 DB (새롭게 추가)

# ✅ 로그 파일 경로
WALLET_LOG_FILE = os.path.join(LOG_DIR, "wallet_log.txt")
TRADES_LOG_FILE = os.path.join(LOG_DIR, "trades_log.txt")

# ✅ 거래 시장 설정 (기본값)
MARKET = "KRW-BTC"
