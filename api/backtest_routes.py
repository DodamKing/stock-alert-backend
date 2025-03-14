from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import logging
import re

# 로깅 설정
logger = logging.getLogger("stock-api.backtest")

# 라우터 생성
router = APIRouter(
    prefix="/api/backtest",
    tags=["backtest"],
    responses={404: {"description": "Not found"}},
)


# 백테스팅 모델 정의
class BacktestDCARequest(BaseModel):
    symbols: List[str] = Field(..., description="종목 코드 목록")
    allocation: Dict[str, float] = Field(..., description="각 종목별 투자 비중 (%)")
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(
        None, description="종료일 (YYYY-MM-DD), 기본값은 오늘"
    )
    initial_amount: float = Field(
        1000000, description="초기 투자 금액 (원), 기본값 100만원"
    )
    investment_amount: float = Field(
        100000, description="정기 투자 금액 (원), 기본값 10만원"
    )
    investment_frequency: str = Field(
        "monthly", description="투자 주기 (monthly, quarterly, yearly)"
    )
    fee_rate: float = Field(0.015, description="매매 수수료율 (%), 기본값 0.015%")
    tax_rate: float = Field(0.3, description="양도소득세율 (%), 기본값 0.3%")


def convert_numpy_types(obj):
    """NumPy 데이터 타입을 Python 기본 타입으로 변환"""
    import numpy as np

    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        return {key: convert_numpy_types(value) for key, value in obj.__dict__.items()}
    else:
        return obj

# 과거 가격 데이터 가져오기 엔드포인트
@router.get("/historical-prices")
async def get_historical_prices(
    symbols: str = Query(
        ..., description="쉼표로 구분된 주식 심볼 목록 (예: '005930,035720,AAPL')"
    ),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(
        None, description="종료일 (YYYY-MM-DD), 기본값은 오늘"
    ),
    interval: str = Query("1d", description="데이터 간격 (1d: 일별, 1m: 월별)"),
):
    """
    여러 종목의 과거 가격 데이터를 반환합니다. 백테스팅에 사용됩니다.

    - **symbols**: 쉼표로 구분된 종목 코드 목록 (예: '005930,035720,AAPL')
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD), 지정하지 않으면 오늘
    - **interval**: 데이터 간격 (1d: 일별, 1m: 월별)

    여러 종목의 시계열 가격 데이터를 반환합니다.
    """
    try:
        logger.info(
            f"과거 가격 데이터 요청: symbols={symbols}, start_date={start_date}, end_date={end_date}, interval={interval}"
        )

        # 종료일 설정 (지정되지 않은 경우 오늘)
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 심볼 리스트로 변환
        symbol_list = [s.strip() for s in symbols.split(",")]

        results = {}

        for symbol in symbol_list:
            try:
                # 시장 정보 자동 감지 (패턴 기반)
                determined_market = None
                if symbol.isdigit() or (len(symbol) == 6 and symbol.isalnum()):
                    # 한국 주식 패턴
                    potential_markets = ["KOSPI", "KOSDAQ", "ETF/KR"]
                elif re.match(r"^[A-Z]+$", symbol):
                    # 미국 주식 패턴
                    potential_markets = ["NASDAQ", "NYSE", "AMEX", "ETF/US"]
                else:
                    potential_markets = [
                        "KOSPI",
                        "KOSDAQ",
                        "ETF/KR",
                        "NASDAQ",
                        "NYSE",
                        "AMEX",
                        "ETF/US",
                    ]

                # 주가 데이터 가져오기
                df = fdr.DataReader(symbol, start_date, end_date)

                if df.empty:
                    logger.warning(f"심볼 {symbol}에 대한 데이터를 찾을 수 없습니다.")
                    continue

                # 마켓 데이터 및 종목명 찾기
                stock_name = None
                for potential_market in potential_markets:
                    try:
                        market_list = fdr.StockListing(potential_market)
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
                            matching = market_list[market_list[symbol_col] == symbol]
                            if not matching.empty:
                                determined_market = potential_market
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

                # 간격 처리 (월별 데이터의 경우 리샘플링)
                if interval == "1m":
                    # 월별 데이터로 리샘플링
                    df = df.resample("M").last()

                # 결과 구성
                prices_data = {
                    "dates": df.index.strftime("%Y-%m-%d").tolist(),
                    "open": (
                        [round(float(x), 2) for x in df["Open"].tolist()]
                        if "Open" in df.columns
                        else None
                    ),
                    "high": (
                        [round(float(x), 2) for x in df["High"].tolist()]
                        if "High" in df.columns
                        else None
                    ),
                    "low": (
                        [round(float(x), 2) for x in df["Low"].tolist()]
                        if "Low" in df.columns
                        else None
                    ),
                    "close": [round(float(x), 2) for x in df["Close"].tolist()],
                    "volume": (
                        [int(x) if not pd.isna(x) else 0 for x in df["Volume"].tolist()]
                        if "Volume" in df.columns
                        else None
                    ),
                }

                results[symbol] = {
                    "name": stock_name,
                    "market": determined_market if determined_market else "UNKNOWN",
                    "data": prices_data,
                    "timeframe": {
                        "start": df.index[0].strftime("%Y-%m-%d"),
                        "end": df.index[-1].strftime("%Y-%m-%d"),
                        "days": (df.index[-1] - df.index[0]).days,
                        "data_points": len(df),
                    },
                }

            except Exception as e:
                logger.error(f"심볼 {symbol} 데이터 처리 중 오류: {str(e)}")
                continue

        if not results:
            raise HTTPException(
                status_code=404,
                detail="요청한 모든 심볼에 대한 데이터를 찾을 수 없습니다.",
            )

        return {
            "status": "success",
            "data": results,
            "symbols_requested": len(symbol_list),
            "symbols_found": len(results),
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"과거 가격 데이터 조회 중 오류 발생: {error_detail}")
        raise HTTPException(
            status_code=500, detail=f"데이터 조회 중 오류 발생: {str(e)}"
        )


# 적립식 투자 백테스팅 엔드포인트
@router.post("/dca")
async def backtest_dca(request: BacktestDCARequest):
    """
    적립식 투자(Dollar Cost Averaging) 전략의 백테스팅을 수행합니다.

    - **symbols**: 종목 코드 목록
    - **allocation**: 각 종목별 투자 비중 (%)
    - **start_date**: 시작일 (YYYY-MM-DD)
    - **end_date**: 종료일 (YYYY-MM-DD), 기본값은 오늘
    - **initial_amount**: 초기 투자 금액 (원)
    - **investment_amount**: 정기 투자 금액 (원)
    - **investment_frequency**: 투자 주기 (monthly, quarterly, yearly)
    - **fee_rate**: 매매 수수료율 (%)
    - **tax_rate**: 양도소득세율 (%)

    백테스팅 결과를 반환합니다.
    """
    try:
        logger.info(
            f"적립식 투자 백테스팅 요청: symbols={request.symbols}, start_date={request.start_date}"
        )

        # 종료일 설정 (지정되지 않은 경우 오늘)
        end_date = (
            request.end_date
            if request.end_date
            else datetime.now().strftime("%Y-%m-%d")
        )

        # 각 종목의 가격 데이터 가져오기
        price_data = {}
        for symbol in request.symbols:
            try:
                df = fdr.DataReader(symbol, request.start_date, end_date)
                if df.empty:
                    logger.warning(f"심볼 {symbol}에 대한 데이터를 찾을 수 없습니다.")
                    continue

                price_data[symbol] = df
            except Exception as e:
                logger.error(f"심볼 {symbol} 데이터 가져오기 중 오류: {str(e)}")
                continue

        if not price_data:
            raise HTTPException(
                status_code=404,
                detail="요청한 종목들에 대한 데이터를 찾을 수 없습니다.",
            )

        # 투자 주기에 따른 날짜 생성
        all_dates = pd.date_range(start=request.start_date, end=end_date)
        if request.investment_frequency == "monthly":
            # 매월 1일에 투자
            investment_dates = pd.date_range(
                start=request.start_date, end=end_date, freq="MS"
            )
        elif request.investment_frequency == "quarterly":
            # 분기별 첫날에 투자
            investment_dates = pd.date_range(
                start=request.start_date, end=end_date, freq="QS"
            )
        elif request.investment_frequency == "yearly":
            # 매년 1월 1일에 투자
            investment_dates = pd.date_range(
                start=request.start_date, end=end_date, freq="AS"
            )
        else:
            # 기본값: 월별
            investment_dates = pd.date_range(
                start=request.start_date, end=end_date, freq="MS"
            )

        # 백테스팅 실행
        portfolio = {}
        transactions = []
        portfolio_value_history = []
        total_invested = 0.0
        cash = request.initial_amount if request.initial_amount > 0 else 0

        # 초기 투자 처리
        if request.initial_amount > 0:
            initial_date = all_dates[0]
            initial_transaction = {
                "date": initial_date.strftime("%Y-%m-%d"),
                "type": "initial",
                "amount": request.initial_amount,
                "details": {},
            }

            # 각 종목별 초기 투자
            for symbol in request.symbols:
                if symbol not in price_data:
                    continue

                allocation_pct = request.allocation.get(symbol, 0) / 100.0
                if allocation_pct <= 0:
                    continue

                invest_amount = request.initial_amount * allocation_pct
                price = (
                    price_data[symbol]
                    .loc[price_data[symbol].index >= initial_date]
                    .iloc[0]["Close"]
                )
                fee = invest_amount * (request.fee_rate / 100.0)
                shares = (invest_amount - fee) / price

                # 포트폴리오 업데이트
                if symbol not in portfolio:
                    portfolio[symbol] = {"shares": 0, "cost_basis": 0}

                portfolio[symbol]["shares"] += shares
                portfolio[symbol]["cost_basis"] += invest_amount

                # 거래 상세정보 기록
                initial_transaction["details"][symbol] = {
                    "price": price,
                    "shares": shares,
                    "amount": invest_amount,
                    "fee": fee,
                }

            transactions.append(initial_transaction)
            total_invested += request.initial_amount

        # 정기 투자 처리
        for inv_date in investment_dates:
            # 이 날짜의 투자 내역
            transaction = {
                "date": inv_date.strftime("%Y-%m-%d"),
                "type": "regular",
                "amount": request.investment_amount,
                "details": {},
            }

            # 각 종목별 투자
            for symbol in request.symbols:
                if symbol not in price_data:
                    continue

                # 해당 날짜 이후의 첫 거래일 찾기
                valid_dates = price_data[symbol].index[
                    price_data[symbol].index >= inv_date
                ]
                if len(valid_dates) == 0:
                    continue

                trade_date = valid_dates[0]

                allocation_pct = request.allocation.get(symbol, 0) / 100.0
                if allocation_pct <= 0:
                    continue

                invest_amount = request.investment_amount * allocation_pct
                price = price_data[symbol].loc[trade_date]["Close"]
                fee = invest_amount * (request.fee_rate / 100.0)
                shares = (invest_amount - fee) / price

                # 포트폴리오 업데이트
                if symbol not in portfolio:
                    portfolio[symbol] = {"shares": 0, "cost_basis": 0}

                portfolio[symbol]["shares"] += shares
                portfolio[symbol]["cost_basis"] += invest_amount

                # 거래 상세정보 기록
                transaction["details"][symbol] = {
                    "price": price,
                    "shares": shares,
                    "amount": invest_amount,
                    "fee": fee,
                }

            transactions.append(transaction)
            total_invested += request.investment_amount

            # 이 날짜의 포트폴리오 가치 계산
            portfolio_value = 0
            for symbol, holdings in portfolio.items():
                if symbol not in price_data:
                    continue

                # 해당 날짜 이후의 첫 거래일 찾기
                valid_dates = price_data[symbol].index[
                    price_data[symbol].index >= inv_date
                ]
                if len(valid_dates) == 0:
                    continue

                valuation_date = valid_dates[0]
                price = price_data[symbol].loc[valuation_date]["Close"]
                value = holdings["shares"] * price
                portfolio_value += value

            # 포트폴리오 가치 기록
            portfolio_value_history.append(
                {
                    "date": inv_date.strftime("%Y-%m-%d"),
                    "value": portfolio_value,
                    "invested": total_invested,
                }
            )

        # 최종 포트폴리오 가치 계산
        final_portfolio = []
        final_value = 0

        for symbol, holdings in portfolio.items():
            if symbol not in price_data:
                continue

            # 마지막 가격 사용
            last_price = price_data[symbol]["Close"].iloc[-1]
            value = holdings["shares"] * last_price
            final_value += value

            # 종목 이름 찾기
            stock_name = None
            try:
                # 적절한 시장에서 종목명 찾기
                if symbol.isdigit() or (len(symbol) == 6 and symbol.isalnum()):
                    # 한국 주식 패턴
                    potential_markets = ["KOSPI", "KOSDAQ", "ETF/KR"]
                else:
                    # 미국 주식 패턴
                    potential_markets = ["NASDAQ", "NYSE", "AMEX", "ETF/US"]

                for market in potential_markets:
                    try:
                        stock_list = fdr.StockListing(market)
                        symbol_col = next(
                            (
                                col
                                for col in ["Symbol", "Code", "code", "symbol", "티커"]
                                if col in stock_list.columns
                            ),
                            None,
                        )
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
                                if col in stock_list.columns
                            ),
                            None,
                        )

                        if symbol_col and name_col:
                            matching = stock_list[stock_list[symbol_col] == symbol]
                            if not matching.empty:
                                stock_name = matching.iloc[0][name_col]
                                break
                    except:
                        continue
            except:
                pass

            final_portfolio.append(
                {
                    "symbol": symbol,
                    "name": stock_name,
                    "shares": holdings["shares"],
                    "cost_basis": holdings["cost_basis"],
                    "current_price": last_price,
                    "current_value": value,
                    "weight": value / final_value * 100 if final_value > 0 else 0,
                    "profit_loss": value - holdings["cost_basis"],
                    "profit_loss_pct": (
                        (value / holdings["cost_basis"] - 1) * 100
                        if holdings["cost_basis"] > 0
                        else 0
                    ),
                }
            )

        # 수익률 계산
        total_profit = final_value - total_invested
        total_profit_pct = (
            (final_value / total_invested - 1) * 100 if total_invested > 0 else 0
        )

        # 투자 기간 계산
        start_date_obj = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        investment_days = (end_date_obj - start_date_obj).days
        investment_years = investment_days / 365.25

        # 연율화 수익률 계산 (CAGR)
        cagr = (
            (pow(final_value / total_invested, 1 / investment_years) - 1) * 100
            if total_invested > 0 and investment_years > 0
            else 0
        )

        # 결과 반환
        result = convert_numpy_types(
            {
                "summary": {
                    "start_date": request.start_date,
                    "end_date": end_date,
                    "investment_period": {
                        "days": investment_days,
                        "years": investment_years,
                        "months": investment_days / 30.44,
                    },
                    "total_invested": total_invested,
                    "final_value": final_value,
                    "total_profit": total_profit,
                    "total_profit_pct": total_profit_pct,
                    "cagr": cagr,
                    "transactions_count": len(transactions),
                },
                "portfolio": sorted(
                    final_portfolio, key=lambda x: x["current_value"], reverse=True
                ),
                "transactions": transactions,
                "value_history": portfolio_value_history,
            }
        )

        return {"status": "success", "data": result}

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = str(e) + "\n" + traceback.format_exc()
        logger.error(f"적립식 투자 백테스팅 중 오류 발생: {error_detail}")
        raise HTTPException(status_code=500, detail=f"백테스팅 중 오류 발생: {str(e)}")
