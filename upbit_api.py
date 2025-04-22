import requests
import jwt
import uuid
import hashlib
import requests
import pandas as pd
from urllib.parse import urlencode
from config import ACCESS_KEY, SECRET_KEY, SERVER_URL, MARKET
from logger import save_to_trades_log

def get_headers(query=None):
    """JWT 토큰 생성"""
    payload = {
        'access_key': ACCESS_KEY,
        'nonce': str(uuid.uuid4()),
    }
    if query:
        query_string = urlencode(query).encode()
        m = hashlib.sha512()
        m.update(query_string)
        payload['query_hash'] = m.hexdigest()
        payload['query_hash_alg'] = 'SHA512'

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return {"Authorization": f"Bearer {token}"}

def get_balance(currency=None):
    """현재 보유 자산 조회"""
    url = f"{SERVER_URL}/v1/accounts"
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        balances = response.json()
        if currency:  # 특정 코인 잔고 조회 (예: BTC, KRW)
            for asset in balances:
                if asset["currency"] == currency:
                    return float(asset["balance"])
            return 0  # 해당 코인 잔고 없음
        return balances  # 전체 잔고 반환
    else:
        print("⚠️ 보유 자산 조회 실패:", response.json())
        return None

def get_market_price(market=None):
    """현재 시세 조회 (업비트 API)"""
    if market is None:
        market = MARKET  # 기본값으로 `MARKET` 사용
    
    url = f"{SERVER_URL}/v1/ticker"
    params = {"markets": market}
    response = requests.get(url, params=params, headers=get_headers())

    if response.status_code == 200:
        return response.json()[0]["trade_price"]  # 현재 거래 가격 반환
    else:
        print(f"⚠️ {market} 시세 조회 실패:", response.json())
        return 0  # 오류 발생 시 0 반환
    
def get_ohlcv(market, count=200):
    """OHLCV 데이터 가져오기 (기본 200개)"""
    url = f"{SERVER_URL}/v1/candles/minutes/1"
    params = {
        "market": market,
        "count": count
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()  # JSON 형태로 반환
    else:
        print(f"⚠️ OHLCV 데이터 요청 실패: {response.json()}")
        return None

def calculate_rsi(data, period=14):
    """RSI (Relative Strength Index) 계산"""
    if not isinstance(data, pd.Series):
        data = pd.Series(data)  # ✅ 리스트를 Pandas Series로 변환

    delta = data.diff()  # 변화량 계산
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()  # 상승분
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()  # 하락분

    rs = gain / loss  # 상대 강도 (Relative Strength)
    rsi = 100 - (100 / (1 + rs))  # RSI 계산

    return rsi.iloc[-1]  # ✅ 최신 RSI 값 반환

def place_order(side="bid", price=None, volume=None, market="KRW-BTC"):
    """
    Upbit에 실제 주문을 보내는 함수.
    - side: "bid" (매수), "ask" (매도)
    - 시장가 매수 시:   side="bid",  price=매수금액, volume=None => ord_type="price"
    - 시장가 매도 시:   side="ask",  price=None,    volume=매도수량 => ord_type="market"
    - 지정가 매수 시:   side="bid",  price=단가,    volume=수량 => ord_type="limit"
    - 지정가 매도 시:   side="ask",  price=단가,    volume=수량 => ord_type="limit"
    """

    url = f"{SERVER_URL}/v1/orders"
    query = {
        "market": market,
        "side": side,
    }

    # 매수 로직
    if side == "bid":
        # 1) 시장가 매수 => price만 있고 volume=None이면 "ord_type"="price"
        if price and volume is None:
            query["ord_type"] = "price"
            query["price"] = str(price)

        # 2) 지정가 매수 => price와 volume 모두 있으면 "ord_type"="limit"
        elif price and volume:
            query["ord_type"] = "limit"
            query["price"] = str(price)
            query["volume"] = str(volume)
        else:
            print("⚠️ 잘못된 매수 주문 (price 또는 volume 확인 필요)")
            return None

    # 매도 로직
    else:  # side == "ask"
        # 3) 시장가 매도 => volume만 있고 price=None이면 "ord_type"="market"
        if volume and price is None:
            query["ord_type"] = "market"
            query["volume"] = str(volume)

        # 4) 지정가 매도 => price와 volume 모두 있으면 "ord_type"="limit"
        elif price and volume:
            query["ord_type"] = "limit"
            query["price"] = str(price)
            query["volume"] = str(volume)
        else:
            print("⚠️ 잘못된 매도 주문 (price 또는 volume 확인 필요)")
            return None

    # 실제 요청
    headers = get_headers(query)
    response = requests.post(url, headers=headers, params=query)

    if response.status_code == 201:
        data = response.json()
        print(f"✅ 주문 완료: {data}")
        return data
    else:
        print(f"⚠️ 주문 실패: {response.status_code}, {response.text}")
        return None

    
def get_trade_history(market="KRW-BTC", count=200):
    """최근 체결된 거래 내역 가져오기"""
    url = f"{SERVER_URL}/v1/trades/ticks"
    params = {"market": market, "count": count}
    response = requests.get(url, params=params, headers=get_headers())

    if response.status_code == 200:
        return response.json()
    else:
        print(f"⚠️ {market} 거래 내역 조회 실패:", response.json())
        return None

def calculate_moving_average(data, short_window=7, long_window=25):
    """이동평균선(MA) 계산"""
    if isinstance(data, list):  
        data = pd.DataFrame(data)  # ✅ 리스트를 DataFrame으로 변환

    # ✅ 데이터 확인 후 'trade_price' 컬럼이 있는지 체크
    if "trade_price" not in data.columns:
        raise KeyError("❌ 'trade_price' 컬럼이 없습니다. 데이터 형식을 확인하세요!")

    data["short_MA"] = data["trade_price"].rolling(window=short_window).mean()
    data["long_MA"] = data["trade_price"].rolling(window=long_window).mean()
    
    return data.iloc[-1]["short_MA"], data.iloc[-1]["long_MA"]  # 최신 MA 값 반환
def calculate_volatility_breakout(data, k=0.5):
    """변동성 돌파 전략 계산"""
    if isinstance(data, list):  
        data = pd.DataFrame(data)  # ✅ 리스트를 DataFrame으로 변환
    
    yesterday = data.iloc[-2]  # ✅ 어제의 데이터 가져오기
    target_price = yesterday["trade_price"] + (yesterday["high_price"] - yesterday["low_price"]) * k
    return target_price  # 목표 매수 가격 반환