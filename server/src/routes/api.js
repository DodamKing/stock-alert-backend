const router = require('express').Router()
const axios = require('axios')
const config = require('../config/config')

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
        const { query, markets, limit } = req.query

        if (!query) {
            return res.status(400).json({
                status: 'error',
                message: '검색할 주식 이름이 필요합니다.',
            })
        }

        // FastAPI의 /api/search 엔드포인트 호출
        let url = `/api/search?query=${encodeURIComponent(query)}`
        if (markets) url += `&markets=${encodeURIComponent(markets)}`
        if (limit) url += `&limit=${encodeURIComponent(limit)}`
        
        console.log(`FastAPI 요청 URL: ${url}`)
        const response = await fastApiClient.get(url)

        // 검색 결과 가공 - 종목 유형 추가
        const results = response.data.results.map(item => {
            // 시장 정보를 기반으로 종목 유형 추가
            let type = 'stock'
            if (item.market.includes('KOSPI') || item.market.includes('KOSDAQ')) {
                type = 'kr-stock'
            } else if (item.market.includes('ETF')) {
                type = 'etf'
            } else if (item.market.includes('NASDAQ') || item.market.includes('NYSE') || item.market.includes('AMEX')) {
                type = 'us-stock'
            }
            
            return {
                ...item,
                type
            }
        })

        res.json({
            status: 'success',
            data: results,
            count: response.data.count,
            query: response.data.query,
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