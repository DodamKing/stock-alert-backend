from fastapi import FastAPI, HTTPException
import FinanceDataReader as fdr
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

app = FastAPI(
    title="Stock Data API",
    description="실시간 주가 데이터를 제공하는 API",
    version="1.0.0",
)


class StockRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class StockPriceResponse(BaseModel):
    symbol: str
    data: List[Dict[str, Any]]


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


@app.get("/api/available-symbols")
async def get_available_symbols():
    # 한국 주식(KOSPI, KOSDAQ) 목록 가져오기
    try:
        kospi = fdr.StockListing("KOSPI")
        kosdaq = fdr.StockListing("KOSDAQ")

        # 데이터프레임 컬럼 확인 및 처리
        # 최근 FinanceDataReader 업데이트에 따라 컬럼명이 변경될 수 있음
        # 가능한 컬럼명 매핑
        column_mappings = {
            "Symbol": ["Symbol", "Code", "code", "symbol"],
            "Name": ["Name", "Name(KOR)", "name", "korean_name"],
            "Market": ["Market", "market"],
        }

        result = []

        # KOSPI 처리
        for df, market_name in [(kospi, "KOSPI"), (kosdaq, "KOSDAQ")]:
            # 컬럼 이름 확인
            columns = df.columns.tolist()
            print(f"Available columns for {market_name}: {columns}")

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
