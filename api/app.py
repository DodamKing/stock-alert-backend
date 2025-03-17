from fastapi import FastAPI, HTTPException, Query, Path
import FinanceDataReader as fdr
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import re

from backtest_routes import router as backtest_router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("stock-api")

app = FastAPI(
    title="Stock Data API",
    description="국내 및 해외 주식, ETF의 데이터를 제공하는 API",
    version="1.0.0",
)

app.include_router(backtest_router)

# ======== 모델 정의 ========
class StockSymbol(BaseModel):
    symbol: str
    name: str
    market: str

# 종목 리스트를 위한 모델 정의
class StocksListResponse(BaseModel):
    market: str
    stocks: List[StockSymbol]
    count: int

class SearchResponse(BaseModel):
    query: str
    results: List[StockSymbol]
    count: int

class StockData(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: str
    current_price: float
    peak_price: float
    peak_date: str
    days_analyzed: int
    last_update: str

# ======== 헬퍼 함수 ========
def get_market_code(market: str) -> str:
    """표준화된 시장 코드 반환"""
    market_upper = market.upper()
    
    if market_upper in ["KOSPI", "KS", "KRX"]:
        return "KOSPI"
    elif market_upper in ["KOSDAQ", "KQ"]:
        return "KOSDAQ"
    elif market_upper in ["NASDAQ", "NQ"]:
        return "NASDAQ"
    elif market_upper in ["NYSE", "NY"]:
        return "NYSE"
    elif market_upper in ["AMEX"]:
        return "AMEX"
    elif market_upper in ["ETF", "ETFS", "ETF/KR", "ETF_KR"]:
        return "ETF/KR"
    elif market_upper in ["ETF/US", "ETF_US"]:
        return "ETF/US"
    else:
        return market_upper

def get_stock_name(symbol: str, market: str) -> Optional[str]:
    """심볼에 해당하는 주식 이름 조회"""
    try:
        if market in ["KOSPI", "KOSDAQ"]:
            # 한국 주식
            listings = fdr.StockListing(market)
            name_col = next((col for col in ["Name", "Name(KOR)", "korean_name", "종목명"] if col in listings.columns), None)
            code_col = next((col for col in ["Symbol", "Code", "code", "symbol", "티커"] if col in listings.columns), None)
            
            if name_col and code_col:
                name_data = listings[listings[code_col] == symbol]
                if not name_data.empty:
                    return name_data.iloc[0][name_col]
        elif market == "ETF":
            # ETF
            listings = fdr.StockListing("ETF")
            name_col = next((col for col in ["Name", "종목명"] if col in listings.columns), None)
            code_col = next((col for col in ["Symbol", "Code", "code", "symbol", "티커"] if col in listings.columns), None)
            
            if name_col and code_col:
                name_data = listings[listings[code_col] == symbol]
                if not name_data.empty:
                    return name_data.iloc[0][name_col]
        elif market in ["NASDAQ", "NYSE", "DOW"]:
            # 미국 주식
            listings = fdr.StockListing(market)
            name_data = listings[listings['Symbol'] == symbol]
            if not name_data.empty:
                return name_data.iloc[0]['Name']
    except Exception as e:
        logger.warning(f"종목명 조회 실패: {str(e)}")
    
    return None

# ======== API 엔드포인트 ========
@app.get("/")
async def root():
    """서버 상태 확인 API"""
    return {"status": "online", "message": "주식 데이터 API 서버가 정상적으로 작동 중입니다."}

@app.get("/api/search", response_model=SearchResponse)
async def search_stocks(
    query: str = Query(..., description="검색할 주식 이름이나 심볼"),
    markets: Optional[str] = Query(None, description="검색할 시장 (쉼표로 구분, 예: KOSPI,NASDAQ,ETF/KR)"),
    limit: int = Query(30, description="최대 결과 수")
):
    """
    주식 이름이나 심볼로 검색하여 관련 종목 목록을 반환합니다.
    
    - **query**: 검색어 (주식 이름 또는 심볼의 일부)
    - **markets**: 검색할 시장 (쉼표로 구분, 지정하지 않으면 모든 시장에서 검색)
    - **limit**: 반환할 최대 결과 수
    
    한국 주식, 미국 주식, ETF 모두 검색 가능합니다.
    """
    try:
        logger.info(f"주식 검색 요청: 검색어={query}, 시장={markets}")

        # 검색할 시장 목록 설정
        markets_to_search = []
        if markets:
            # 사용자가 지정한 시장 목록
            raw_markets = [m.strip().upper() for m in markets.split(",")]
            markets_to_search = [get_market_code(m) for m in raw_markets]
        else:
            # 기본 시장 목록 (DOW 제외)
            markets_to_search = ["KOSPI", "KOSDAQ", "NASDAQ", "NYSE", "AMEX", "ETF/KR", "ETF/US"]

        result = []

        # 각 시장별 검색
        for market_name in markets_to_search:
            try:
                # ETF 시장인 경우 별도 처리
                if market_name in ["ETF/KR", "ETF/US"]:
                    try:
                        # ETF 목록 가져오기
                        etf_df = fdr.StockListing(market_name)

                        # 컬럼 확인
                        etf_columns = etf_df.columns.tolist()
                        logger.info(f"{market_name} 컬럼: {etf_columns}")

                        # ETF 목록에서 적절한 티커와 이름 컬럼 찾기
                        ticker_col = next((col for col in ["티커", "Symbol", "Code", "code", "symbol"] if col in etf_columns), None)
                        name_col = next((col for col in ["종목명", "Name", "name"] if col in etf_columns), None)

                        if ticker_col and name_col:
                            # 검색어로 필터링
                            query_lower = query.lower()

                            for _, row in etf_df.iterrows():
                                # 티커에서 검색
                                ticker_match = False
                                if str(row[ticker_col]).lower().find(query_lower) >= 0:
                                    ticker_match = True

                                # 이름에서 검색
                                name_match = False
                                if str(row[name_col]).lower().find(query_lower) >= 0:
                                    name_match = True

                                # 티커 또는 이름이 일치하면 결과에 추가
                                if ticker_match or name_match:
                                    item = {
                                        "symbol": str(row[ticker_col]),
                                        "name": str(row[name_col]),
                                        "market": market_name
                                    }
                                    result.append(item)
                    except Exception as e:
                        logger.error(f"ETF ({market_name}) 검색 중 오류 발생: {str(e)}")
                else:
                    # 일반 주식 목록 가져오기
                    df = fdr.StockListing(market_name)

                    # 컬럼 이름 확인
                    columns = df.columns.tolist()

                    # 가능한 심볼과 이름 컬럼 찾기
                    symbol_col = next((col for col in ["Symbol", "Code", "code", "symbol"] if col in columns), None)
                    name_cols = [col for col in ["Name", "Name(KOR)", "korean_name", "name"] if col in columns]

                    if not symbol_col or not name_cols:
                        logger.warning(f"시장 {market_name}에서 적절한 컬럼을 찾을 수 없습니다. 컬럼: {columns}")
                        continue

                    # 검색어로 필터링 (대소문자 구분 없이)
                    query_lower = query.lower()

                    for _, row in df.iterrows():
                        # 심볼에서 검색
                        symbol_match = False
                        if symbol_col and str(row[symbol_col]).lower().find(query_lower) >= 0:
                            symbol_match = True

                        # 이름에서 검색
                        name_match = False
                        for name_col in name_cols:
                            if name_col in row.index and str(row[name_col]).lower().find(query_lower) >= 0:
                                name_match = True
                                break

                        # 심볼 또는 이름이 일치하면 결과에 추가
                        if symbol_match or name_match:
                            item = {
                                "symbol": str(row[symbol_col]),
                                "name": str(row[name_cols[0]]),
                                "market": market_name
                            }
                            result.append(item)
            except Exception as e:
                # 특정 시장 검색 중 오류가 발생하면 로그만 남기고 계속 진행
                logger.error(f"시장 {market_name} 검색 중 오류 발생: {str(e)}")
                continue

        # 결과가 너무 많으면 상위 N개만 반환
        if len(result) > limit:
            result = result[:limit]

        logger.info(f"검색 결과: {len(result)}개 항목 찾음")
        return {"query": query, "results": result, "count": len(result)}

    except Exception as e:
        import traceback
        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"검색 중 오류 발생: {error_detail}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@app.get("/api/stock-data")
async def get_stock_data(
    symbol: str = Query(..., description="주식 심볼"),
    market: Optional[str] = Query(
        None, description="시장 (KOSPI, KOSDAQ, NASDAQ, NYSE, ETF/KR 등) - 선택사항"
    ),
    days: int = Query(365, description="분석할 기간(일)"),
):
    """
    특정 종목의 데이터와 전고점 정보를 반환합니다.

    - **symbol**: 종목 코드 (예: '005930', 'AAPL')
    - **market**: 시장 (KOSPI, KOSDAQ, NASDAQ, NYSE, ETF/KR 등) - 선택사항
    - **days**: 분석할 기간(일) (기본: 365일)

    전고점, 현재가, 날짜 등의 데이터를 반환합니다.
    시장 정보를 제공하지 않으면 자동으로 심볼에 맞는 시장을 찾습니다.
    """
    try:
        logger.info(f"주식 데이터 요청: symbol={symbol}, market={market}, days={days}")

        # 시장 코드 변환 (제공된 경우)
        determined_market = get_market_code(market) if market else None

        # 데이터 가져오기
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # DataReader는 모든 종류(일반 주식, ETF)에 동일하게 사용
        try:
            df = fdr.DataReader(
                symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )
        except Exception as e:
            logger.error(f"주식 데이터 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=404, detail=f"데이터를 찾을 수 없습니다: {symbol}"
            )

        if df.empty:
            logger.warning(f"심볼 {symbol}에 대한 데이터를 찾을 수 없습니다.")
            raise HTTPException(
                status_code=404, detail=f"데이터를 찾을 수 없습니다: {symbol}"
            )

        # 전고점 찾기
        peak_value = df["High"].max()
        peak_index = df["High"].idxmax()

        # 현재 가격
        current_price = df["Close"].iloc[-1]

        # 종목 이름과 시장 정보 찾기
        stock_name = None

        # 시장 정보가 없는 경우 자동으로 찾기 시도
        if not determined_market:
            # 심볼 패턴에 따라 검색 순서 최적화
            if symbol.isdigit() or (len(symbol) == 6 and symbol.isalnum()):
                # 숫자만 있거나 국내 종목 코드 패턴(6자리)인 경우 - 국내 시장 우선
                potential_markets = [
                    "KOSPI",
                    "KOSDAQ",
                    "ETF/KR",
                    "NASDAQ",
                    "NYSE",
                    "AMEX",
                    "ETF/US",
                ]
                logger.info(f"국내 종목 코드 패턴 감지: {symbol} - 국내 시장 우선 검색")
            elif re.match(r"^[A-Z]+$", symbol):
                # 대문자 알파벳만 있는 경우 - 미국 시장 우선
                potential_markets = [
                    "NASDAQ",
                    "NYSE",
                    "AMEX",
                    "ETF/US",
                    "KOSPI",
                    "KOSDAQ",
                    "ETF/KR",
                ]
                logger.info(f"미국 종목 코드 패턴 감지: {symbol} - 미국 시장 우선 검색")
            else:
                # 그 외 패턴 - 모든 시장 검색
                potential_markets = [
                    "KOSPI",
                    "KOSDAQ",
                    "ETF/KR",
                    "NASDAQ",
                    "NYSE",
                    "AMEX",
                    "ETF/US",
                ]
                logger.info(f"일반 패턴 감지: {symbol} - 일반 순서로 검색")

            # 각 시장에서 심볼 찾기 시도
            for potential_market in potential_markets:
                try:
                    market_list = fdr.StockListing(potential_market)

                    # 시장 목록에서 적절한 심볼 컬럼 찾기
                    market_columns = market_list.columns.tolist()
                    symbol_col = next(
                        (
                            col
                            for col in ["Symbol", "Code", "code", "symbol", "티커"]
                            if col in market_columns
                        ),
                        None,
                    )

                    if symbol_col:
                        # 심볼로 종목 찾기
                        matching = market_list[market_list[symbol_col] == symbol]
                        if not matching.empty:
                            determined_market = potential_market
                            # 종목명 컬럼 찾기
                            name_col = next(
                                (
                                    col
                                    for col in [
                                        "Name",
                                        "Name(KOR)",
                                        "korean_name",
                                        "name",
                                        "종목명",
                                    ]
                                    if col in market_columns
                                ),
                                None,
                            )
                            if name_col:
                                stock_name = matching.iloc[0][name_col]
                            break
                except Exception as e:
                    logger.warning(
                        f"{potential_market} 시장에서 심볼 검색 중 오류: {str(e)}"
                    )
                    continue

        logger.info(f"결정된 시장: {determined_market}")

        # 종목 이름이 찾아지지 않았을 경우 다시 시도
        if not stock_name and determined_market:
            try:
                if determined_market in ["ETF/KR", "ETF/US"]:
                    # ETF 목록에서 종목명 찾기
                    etf_list = fdr.StockListing(determined_market)

                    # ETF 목록에서 적절한 티커와 이름 컬럼 찾기
                    etf_columns = etf_list.columns.tolist()
                    ticker_col = next(
                        (
                            col
                            for col in ["티커", "Symbol", "Code", "code", "symbol"]
                            if col in etf_columns
                        ),
                        None,
                    )
                    name_col = next(
                        (
                            col
                            for col in ["종목명", "Name", "name"]
                            if col in etf_columns
                        ),
                        None,
                    )

                    if ticker_col and name_col:
                        # 티커로 ETF 찾기
                        matching_etf = etf_list[etf_list[ticker_col] == symbol]
                        if not matching_etf.empty:
                            stock_name = matching_etf.iloc[0][name_col]
                else:
                    # 일반 주식 목록에서 종목명 찾기
                    stock_list = fdr.StockListing(determined_market)

                    # 주식 목록에서 적절한 심볼과 이름 컬럼 찾기
                    stock_columns = stock_list.columns.tolist()
                    symbol_col = next(
                        (
                            col
                            for col in ["Symbol", "Code", "code", "symbol"]
                            if col in stock_columns
                        ),
                        None,
                    )
                    name_col = next(
                        (
                            col
                            for col in ["Name", "Name(KOR)", "korean_name", "name"]
                            if col in stock_columns
                        ),
                        None,
                    )

                    if symbol_col and name_col:
                        # 심볼로 주식 찾기
                        matching_stock = stock_list[stock_list[symbol_col] == symbol]
                        if not matching_stock.empty:
                            stock_name = matching_stock.iloc[0][name_col]
            except Exception as e:
                logger.warning(f"종목명 조회 실패: {str(e)}")

        # 응답 데이터 구성
        response = {
            "symbol": symbol,
            "name": stock_name,
            "market": determined_market if determined_market else "UNKNOWN",
            "current_price": float(current_price),
            "peak_price": float(peak_value),
            "peak_date": peak_index.strftime("%Y-%m-%d"),
            "days_analyzed": days,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # 차트용 시계열 데이터 추가
            "chart_data": {
                "dates": df.index.strftime("%Y-%m-%d").tolist(),
                "prices": {"close": [round(float(x), 2) for x in df["Close"].tolist()]},
            },
        }

        logger.info(f"{symbol} 데이터 반환: 현재가={current_price}, 고점={peak_value}")
        return response

    except HTTPException:
        # 이미 처리된 HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        import traceback

        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"주식 데이터 조회 중 오류 발생: {error_detail}")
        raise HTTPException(
            status_code=500, detail=f"데이터 조회 중 오류 발생: {str(e)}"
        )


@app.get("/api/market-symbols/{market}", response_model=StocksListResponse)
async def get_market_symbols(
    market: str = Path(
        ..., description="시장 코드 (KOSPI, KOSDAQ, NASDAQ, NYSE, ETF/KR 등)"
    ),
    limit: int = Query(
        None, description="최대 결과 수 (지정하지 않으면 모든 종목 반환)"
    ),
):
    """
    특정 시장에 속한 모든 종목 목록을 반환합니다.

    - **market**: 시장 코드 (KOSPI, KOSDAQ, NASDAQ, NYSE, ETF/KR 등)
    - **limit**: 최대 결과 수 (지정하지 않으면 모든 종목 반환)

    종목 코드(심볼)와 이름이 포함된 목록을 반환합니다.
    """
    try:
        logger.info(f"시장 종목 목록 요청: market={market}")

        # 시장 코드 표준화
        standard_market = get_market_code(market)

        try:
            # fdr을 통해 시장 종목 목록 가져오기
            df = fdr.StockListing(standard_market)

            if df.empty:
                logger.warning(f"시장 {standard_market}에 대한 종목이 없습니다.")
                raise HTTPException(
                    status_code=404,
                    detail=f"시장 {standard_market}에 대한 종목을 찾을 수 없습니다.",
                )

            # 컬럼 이름 확인
            columns = df.columns.tolist()
            logger.info(f"시장 {standard_market} 데이터 컬럼: {columns}")

            # 가능한 심볼과 이름 컬럼 찾기
            symbol_col = next(
                (
                    col
                    for col in ["Symbol", "Code", "code", "symbol", "티커"]
                    if col in columns
                ),
                None,
            )
            name_col = next(
                (
                    col
                    for col in ["Name", "Name(KOR)", "korean_name", "name", "종목명"]
                    if col in columns
                ),
                None,
            )

            if not symbol_col or not name_col:
                logger.warning(
                    f"시장 {standard_market}에서 적절한 컬럼을 찾을 수 없습니다. 컬럼: {columns}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"시장 {standard_market}의 데이터 형식을 처리할 수 없습니다. 관리자에게 문의하세요.",
                )

            # 결과 리스트 생성
            result = []
            for _, row in df.iterrows():
                symbol = str(row[symbol_col])
                name = str(row[name_col])

                item = StockSymbol(symbol=symbol, name=name, market=standard_market)
                result.append(item)

            # 결과가 너무 많으면 상위 N개만 반환
            if limit and len(result) > limit:
                result = result[:limit]

            logger.info(f"시장 {standard_market} 종목 목록: {len(result)}개 항목 찾음")
            return {"market": standard_market, "stocks": result, "count": len(result)}

        except Exception as e:
            logger.error(
                f"시장 {standard_market} 종목 목록 조회 중 오류 발생: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail=f"종목 목록 조회 중 오류 발생: {str(e)}"
            )

    except HTTPException:
        # 이미 처리된 HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        import traceback

        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"시장 종목 목록 조회 중 오류 발생: {error_detail}")
        raise HTTPException(
            status_code=500, detail=f"종목 목록 조회 중 오류 발생: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    # 서버 시작 로그
    logger.info("🚀 주식 데이터 서버를 시작합니다...")
    logger.info("📊 서버 URL: http://0.0.0.0:8000")
    logger.info("📚 API 문서: http://0.0.0.0:8000/docs")

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
