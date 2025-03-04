from fastapi import FastAPI, HTTPException
import FinanceDataReader as fdr
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

app = FastAPI(
    title="Stock Data API",
    description="국내 및 해외 주식의 실시간 주가 데이터를 제공하는 API",
    version="1.1.0",
)


class StockRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class StockPriceResponse(BaseModel):
    symbol: str
    data: List[Dict[str, Any]]


class RealTimeStockPriceResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    current_price: float
    change: float
    change_percent: float
    volume: int
    timestamp: str


class PeakDropResponse(BaseModel):
    symbol: str
    current_price: float
    peak_price: float
    drop_value: float
    drop_percent: float
    peak_date: str


@app.get("/")
async def root():
    return {"message": "Stock Data API is running"}


@app.post("/api/stock-price", response_model=StockPriceResponse)
async def get_stock_price(request: StockRequest):
    try:
        # FinanceDataReader로 주가 데이터 가져오기
        df = fdr.DataReader(request.symbol, request.start_date, request.end_date)

        # DataFrame을 리스트로 변환 (날짜를 인덱스에서 필드로 변경)
        df.reset_index(inplace=True)
        df["Date"] = df["Date"].astype(str)  # 날짜를 문자열로 변환
        records = df.to_dict("records")

        return {"symbol": request.symbol, "data": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/realtime-price/{symbol}")
async def get_realtime_price(symbol: str):
    """
    특정 종목의 실시간 가격 정보를 반환합니다.
    한국 주식의 경우 'KR'을 접두어로 붙이고, 미국 주식은 그대로 사용합니다.
    예: 삼성전자 = 'KR005930', 애플 = 'AAPL'
    """
    try:
        # 종목 정보 가져오기
        symbol_prefix = ""
        if symbol.startswith("KR"):
            # 한국 주식인 경우 KR 접두어 제거
            symbol_prefix = "KR"
            actual_symbol = symbol[2:]
        else:
            # 해외 주식인 경우 그대로 사용
            actual_symbol = symbol

        # 최근 1일치 데이터 가져오기
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)  # 주말과 휴장일을 고려하여 5일 전부터 조회
        
        df = fdr.DataReader(actual_symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"데이터를 찾을 수 없습니다: {symbol}")
        
        # 가장 최근 데이터 가져오기
        latest_data = df.iloc[-1].copy()
        
        # 하루 전 데이터와 비교하여 변화량 계산
        if len(df) > 1:
            prev_day = df.iloc[-2]
            change = latest_data['Close'] - prev_day['Close']
            change_percent = (change / prev_day['Close']) * 100
        else:
            change = 0
            change_percent = 0
        
        # 종목 이름 가져오기 (가능한 경우)
        stock_name = None
        try:
            if symbol.startswith("KR"):
                # 한국 주식
                market = "KOSPI" if len(actual_symbol) == 6 else "KOSDAQ"  # 간단한 가정: 6자리면 코스피
                listings = fdr.StockListing(market)
                name_col = next((col for col in ["Name", "Name(KOR)", "korean_name"] if col in listings.columns), None)
                code_col = next((col for col in ["Symbol", "Code", "code", "symbol"] if col in listings.columns), None)
                
                if name_col and code_col:
                    name_data = listings[listings[code_col] == actual_symbol]
                    if not name_data.empty:
                        stock_name = name_data.iloc[0][name_col]
            else:
                # 미국 주식
                listings = fdr.StockListing("NASDAQ") if "." not in actual_symbol else fdr.StockListing("NYSE")
                name_data = listings[listings['Symbol'] == actual_symbol]
                if not name_data.empty:
                    stock_name = name_data.iloc[0]['Name']
        except Exception:
            # 종목명 조회 실패시 무시
            pass
        
        response = {
            "symbol": symbol,
            "name": stock_name,
            "current_price": latest_data['Close'],
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": int(latest_data.get('Volume', 0)),
            "timestamp": df.index[-1].strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return response
    except Exception as e:
        import traceback
        error_detail = str(e) + "\n" + traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/peak-drop/{symbol}", response_model=PeakDropResponse)
async def get_peak_drop(symbol: str, days: int = 365):
    """
    특정 종목의 설정 기간(기본 1년) 내 전고점 대비 현재 하락 포인트를 반환합니다.
    
    Parameters:
    - symbol: 종목 코드 (예: 'AAPL', 'KR005930')
    - days: 분석할 기간 (기본값: 365일)
    """
    try:
        # 종목 정보 가져오기
        if symbol.startswith("KR"):
            # 한국 주식인 경우 KR 접두어 제거
            actual_symbol = symbol[2:]
        else:
            # 해외 주식인 경우 그대로 사용
            actual_symbol = symbol

        # 데이터 가져오기
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = fdr.DataReader(actual_symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"데이터를 찾을 수 없습니다: {symbol}")
        
        # 전고점 찾기
        peak_value = df['High'].max()
        peak_index = df['High'].idxmax()
        
        # 현재 가격
        current_price = df['Close'].iloc[-1]
        
        # 하락 포인트 계산
        drop_value = peak_value - current_price
        drop_percent = (drop_value / peak_value) * 100
        
        response = {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "peak_price": round(peak_value, 2),
            "drop_value": round(drop_value, 2),
            "drop_percent": round(drop_percent, 2),
            "peak_date": peak_index.strftime("%Y-%m-%d")
        }
        
        return response
    except Exception as e:
        import traceback
        error_detail = str(e) + "\n" + traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/available-symbols")
async def get_available_symbols():
    # 국내 및 해외 주식 목록 가져오기
    try:
        # 한국 주식(KOSPI, KOSDAQ) 목록
        kospi = fdr.StockListing("KOSPI")
        kosdaq = fdr.StockListing("KOSDAQ")
        
        # 미국 주식(나스닥, NYSE, 다우존스) 목록
        nasdaq = fdr.StockListing("NASDAQ")
        nyse = fdr.StockListing("NYSE")
        dow = fdr.StockListing("DOW")  # 다우존스 산업 평균 지수 구성 종목

        # 데이터프레임 컬럼 확인 및 처리
        # 최근 FinanceDataReader 업데이트에 따라 컬럼명이 변경될 수 있음
        # 가능한 컬럼명 매핑
        column_mappings = {
            "Symbol": ["Symbol", "Code", "code", "symbol"],
            "Name": ["Name", "Name(KOR)", "name", "korean_name"],
            "Market": ["Market", "market"],
        }

        result = []

        # 각 시장별 처리
        for df, market_name in [
            (kospi, "KOSPI"), 
            (kosdaq, "KOSDAQ"),
            (nasdaq, "NASDAQ"),
            (nyse, "NYSE"),
            (dow, "DOW")
        ]:
            # 컬럼 이름 확인
            columns = df.columns.tolist()

            # 각 종목에 대해 필요한 정보 추출
            for _, row in df.iterrows():
                item = {}

                # Symbol 필드 찾기
                for target, possible_names in column_mappings.items():
                    found = False
                    for col_name in possible_names:
                        if col_name in columns:
                            item[target] = row[col_name]
                            found = True
                            break
                    if not found:
                        # 필수 필드가 없으면 기본값 설정
                        item[target] = "Unknown" if target != "Symbol" else row.iloc[0]

                # Market 정보 추가 (없을 경우)
                if item.get("Market") == "Unknown":
                    item["Market"] = market_name
                
                # 한국 주식의 경우 'KR' 접두어 추가
                if market_name in ["KOSPI", "KOSDAQ"]:
                    item["Symbol"] = "KR" + item["Symbol"]

                result.append(item)

        return {"symbols": result}
    except Exception as e:
        import traceback
        error_detail = str(e) + "\n" + traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/market-indices")
async def get_market_indices():
    # 주요 시장 지수 가져오기
    try:
        indices = {
            "kospi": fdr.DataReader("KS11").iloc[-1].to_dict(),  # KOSPI
            "kosdaq": fdr.DataReader("KQ11").iloc[-1].to_dict(),  # KOSDAQ
            "snp500": fdr.DataReader("US500").iloc[-1].to_dict(),  # S&P 500
            "nasdaq": fdr.DataReader("IXIC").iloc[-1].to_dict(),  # NASDAQ
            "dow": fdr.DataReader("DJI").iloc[-1].to_dict(),  # 다우존스 산업평균지수
        }

        # 날짜 형식 조정
        for key in indices:
            if "Date" in indices[key]:
                indices[key]["Date"] = str(indices[key]["Date"])

        return indices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import logging

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("stock-api")

    # 서버 시작 로그
    logger.info("🚀 주가 데이터 서버를 시작합니다...")
    logger.info("📊 서버 URL: http://0.0.0.0:8000")
    logger.info("📚 API 문서: http://0.0.0.0:8000/docs")

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)