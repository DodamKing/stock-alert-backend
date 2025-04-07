const router = require('express').Router()
const axios = require('axios')
const config = require('../config/config')
const fs = require('fs/promises')
const path = require('path')

// 데이터 디렉토리 경로
const DATA_DIR = path.join(__dirname, '../../data')
const MARKET_CODES = require('../config/market_codes')

// FastAPI 클라이언트
const fastApiClient = axios.create({
    baseURL: config.fastApiUrl,
    timeout: 30000, // 30초로 충분히 늘림
    headers: {
        'Content-Type': 'application/json',
    },
})

// FastAPI 서버 상태 확인
router.get('/status', async (req, res, next) => {
    try {
        const response = await fastApiClient.get('/')
        res.json({
            status: 'success',
            message: 'FastAPI 서버에 연결되었습니다.',
            data: response.data,
        })
    } catch (error) {
        next(error)
    }
})

// 1. 주식 이름으로 종목코드(심볼) 검색 API
router.get('/search', async (req, res, next) => {
    try {
        const { query, markets, limit = 30 } = req.query

        if (!query) {
            return res.status(400).json({
                status: 'error',
                message: '검색할 주식 이름이 필요합니다.',
            })
        }

        console.log(`검색 요청: query=${query}, markets=${markets}, limit=${limit}`)

        // 검색할 시장 목록 설정
        let marketsToSearch = MARKET_CODES
        if (markets) {
            const marketList = markets.split(',').map(m => m.trim().toUpperCase())
            marketsToSearch = marketList.map(m => {
                // 시장 코드 변환 (ETF/KR -> KR 등)
                if (m === 'ETF/KR' || m === 'ETF' || m === 'ETFS') return 'ETF_KR'
                if (m === 'ETF/US') return 'ETF_US'
                if (m === 'KS' || m === 'KRX') return 'KOSPI'
                if (m === 'KQ') return 'KOSDAQ'
                if (m === 'NQ') return 'NASDAQ'
                if (m === 'NY') return 'NYSE'
                
                return m
            })
        }

        // 결과 저장 배열
        let results = []

        // 각 시장별로 JSON 파일에서 검색
        for (const marketCode of marketsToSearch) {
            try {
                // JSON 파일 읽기
                const filePath = path.join(DATA_DIR, `${marketCode}.json`)
                const fileData = await fs.readFile(filePath, 'utf8')
                const marketData = JSON.parse(fileData)

                if (!marketData.stocks || !Array.isArray(marketData.stocks)) {
                    console.warn(`${marketCode} 시장 데이터 형식이 올바르지 않습니다.`)
                    continue
                }

                // 검색어로 필터링 (대소문자 구분 없이)
                const queryLower = query.toLowerCase()
                const matchingStocks = marketData.stocks.filter(stock => {
                    const symbolMatch = stock.symbol.toLowerCase().includes(queryLower)
                    const nameMatch = stock.name.toLowerCase().includes(queryLower)
                    return symbolMatch || nameMatch
                })

                // 종목 유형 추가
                const stocksWithType = matchingStocks.map(stock => {
                    // 시장 정보를 기반으로 종목 유형 추가
                    let type = 'stock'
                    if (stock.market.includes('KOSPI') || stock.market.includes('KOSDAQ')) {
                        type = 'kr-stock'
                    } else if (marketCode === 'ETF_KR' || marketCode === 'ETF_US') {
                        type = 'etf'
                    } else if (stock.market.includes('NASDAQ') || stock.market.includes('NYSE') || stock.market.includes('AMEX')) {
                        type = 'us-stock'
                    }

                    return {
                        ...stock,
                        type
                    }
                })

                // 결과에 추가
                results = [...results, ...stocksWithType]
            } catch (error) {
                // JSON 파일이 없는 경우 등의 오류는 무시하고 계속 진행
                console.warn(`${marketCode} 시장 데이터 처리 중 오류:`, error.message)
                continue
            }
        }

        // 결과가 너무 많으면 제한
        if (results.length > limit) {
            results = results.slice(0, parseInt(limit))
        }
        
        console.log(`검색 결과: ${results.length}개 종목 찾음`)

        res.json({
            status: 'success',
            data: results,
            count: results.length,
            query: query,
        })
    } catch (error) {
        console.error('검색 API 오류:', error)
        next(error)
    }
})

// 2. 심볼로 전고점 대비 하락률 계산 API
router.get('/peak-drop', async (req, res, next) => {
    try {
        const { symbol, market, days } = req.query

        if (!symbol) {
            return res.status(400).json({
                status: 'error',
                message: '주식 심볼이 필요합니다.',
            })
        }

        // FastAPI의 /api/stock-data 엔드포인트 호출
        let url = `/api/stock-data?symbol=${encodeURIComponent(symbol)}`
        if (market) url += `&market=${encodeURIComponent(market)}`
        if (days) url += `&days=${encodeURIComponent(days)}`
        
        console.log(`FastAPI 요청 URL: ${url}`)
        const response = await fastApiClient.get(url)
        const stockData = response.data

        // 하락률 계산
        const currentPrice = stockData.current_price
        const peakPrice = stockData.peak_price
        const dropValue = peakPrice - currentPrice
        const dropPercent = (dropValue / peakPrice) * 100
        
        // 종목 타입 결정
        let stockType = 'stock'
        if (stockData.market.includes('KOSPI') || stockData.market.includes('KOSDAQ')) {
            stockType = 'kr-stock'
        } else if (stockData.market.includes('ETF')) {
            stockType = 'etf'
        } else if (stockData.market.includes('NASDAQ') || stockData.market.includes('NYSE') || stockData.market.includes('AMEX')) {
            stockType = 'us-stock'
        }

        // 데이터 가공
        const formattedData = {
            symbol: stockData.symbol,
            name: stockData.name || '알 수 없음',
            market: stockData.market,
            type: stockType,
            currentPrice: currentPrice,
            peakPrice: peakPrice,
            peakDate: stockData.peak_date,
            drop: {
                value: parseFloat(dropValue.toFixed(2)),
                percent: parseFloat(dropPercent.toFixed(2)),
                significance: determineDropSignificance(dropPercent),
            },
            daysAnalyzed: stockData.days_analyzed,
            analysis: generateDropAnalysis(dropPercent, stockType),
            lastUpdate: stockData.last_update,
        }

        res.json({
            status: 'success',
            data: formattedData,
        })
    } catch (error) {
        console.error('전고점 대비 하락률 API 오류:', error)
        next(error)
    }
})

// 3. 차트용 시계열 데이터 제공 API
router.get('/chart-data', async (req, res, next) => {
    try {
        const { symbol, market, days = 365 } = req.query

        if (!symbol) {
            return res.status(400).json({
                status: 'error',
                message: '주식 심볼이 필요합니다.',
            })
        }

        // FastAPI의 /api/stock-data 엔드포인트에서 기본 및 차트 데이터 요청
        let url = `/api/stock-data?symbol=${encodeURIComponent(symbol)}`
        if (market) url += `&market=${encodeURIComponent(market)}`
        if (days) url += `&days=${encodeURIComponent(days)}`

        const response = await fastApiClient.get(url)
        const stockData = response.data

        // 차트 데이터가 없으면 에러 반환
        if (!stockData.chart_data) {
            return res.status(404).json({
                status: 'error',
                message: '차트 데이터를 찾을 수 없습니다.',
            })
        }

        // 차트용 데이터 가공
        const chartData = {
            symbol: stockData.symbol,
            name: stockData.name || '알 수 없음',
            market: stockData.market,
            timeframe: {
                days: stockData.days_analyzed,
                start: stockData.chart_data.dates[0],
                end: stockData.chart_data.dates[stockData.chart_data.dates.length - 1]
            },
            peakInfo: {
                date: stockData.peak_date,
                price: stockData.peak_price
            },
            series: [
                {
                    name: '종가',
                    type: 'line',
                    data: stockData.chart_data.dates.map((date, index) => ({
                        date,
                        value: stockData.chart_data.prices.close[index]
                    }))
                }
            ],
            // 추가 옵션 정보
            options: {
                highlightPeak: true, // 전고점 하이라이트 표시 여부
                annotations: [
                    {
                        type: 'line',
                        yValue: stockData.peak_price,
                        label: '전고점',
                        color: '#FF4560'
                    },
                    {
                        type: 'line',
                        yValue: stockData.current_price,
                        label: '현재가',
                        color: '#00E396'
                    }
                ]
            }
        }

        // OHLC 데이터가 있다면 캔들차트용 데이터도 추가
        if (stockData.chart_data.prices.open &&
            stockData.chart_data.prices.high &&
            stockData.chart_data.prices.low) {

            chartData.series.push({
                name: 'OHLC',
                type: 'candlestick',
                data: stockData.chart_data.dates.map((date, index) => ({
                    date,
                    open: stockData.chart_data.prices.open[index],
                    high: stockData.chart_data.prices.high[index],
                    low: stockData.chart_data.prices.low[index],
                    close: stockData.chart_data.prices.close[index]
                }))
            })
        }

        // 거래량 데이터가 있다면 추가
        if (stockData.chart_data.volume) {
            chartData.series.push({
                name: '거래량',
                type: 'column',
                data: stockData.chart_data.dates.map((date, index) => ({
                    date,
                    value: stockData.chart_data.volume[index]
                }))
            })
        }

        res.json({
            status: 'success',
            data: chartData,
        })
    } catch (error) {
        console.error('차트 데이터 API 오류:', error)
        next(error)
    }
})

// 하락률의 심각성 판단 함수
function determineDropSignificance(dropPercent) {
    if (dropPercent <= 0) {
        return '하락 없음';
    } else if (dropPercent < 5) {
        return '일반적인 변동';
    } else if (dropPercent < 10) {
        return '소폭 조정';
    } else if (dropPercent < 20) {
        return '의미있는 조정';
    } else if (dropPercent < 30) {
        return '큰 폭의 하락';
    } else {
        return '심각한 하락';
    }
}

// 하락률에 따른 분석 코멘트 생성 함수
function generateDropAnalysis(dropPercent, stockType = 'stock') {
    // ETF에 대한 코멘트는 조금 다르게 처리
    const isEtf = stockType === 'etf';
    
    if (dropPercent <= 0) {
        return '현재 전고점 대비 하락이 없습니다.';
    } else if (dropPercent < 5) {
        return `일반적인 시장 변동 범위 내 하락입니다.${isEtf ? ' ETF는 일반적으로 단기 변동성이 낮은 편입니다.' : ''}`;
    } else if (dropPercent < 10) {
        return `소폭 조정 국면으로 관찰이 필요합니다.${isEtf ? ' ETF의 기초자산 동향을 확인해보세요.' : ''}`;
    } else if (dropPercent < 20) {
        if (isEtf) {
            return '의미있는 조정 국면입니다. ETF의 기초자산 및 시장 전반적인 흐름을 함께 분석해볼 필요가 있습니다.';
        } else {
            return '의미있는 조정 국면입니다. 매수 기회를 검토해 볼 수 있습니다.';
        }
    } else if (dropPercent < 30) {
        if (isEtf) {
            return '큰 폭의 하락이 진행 중입니다. ETF가 추종하는 지수나 섹터의 전반적인 약세가 있는지 확인하세요.';
        } else {
            return '큰 폭의 하락이 진행 중입니다. 추가 하락 가능성에 주의하세요.';
        }
    } else {
        if (isEtf) {
            return '매우 심각한 하락 국면입니다. 해당 ETF의 기초 자산군에 구조적 문제가 있는지 확인이 필요합니다.';
        } else {
            return '매우 심각한 하락 국면입니다. 신중한 투자 결정이 필요합니다.';
        }
    }
}

module.exports = router