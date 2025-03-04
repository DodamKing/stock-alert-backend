const router = require('express').Router()
const axios = require('axios')
const config = require('../config/config')

// FastAPI 클라이언트
const fastApiClient = axios.create({
    baseURL: config.fastApiUrl,
    timeout: 5000,
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

// 실시간 주식 가격 정보 조회
router.get('/realtime/:symbol', async (req, res, next) => {
    try {
        const { symbol } = req.params

        if (!symbol) {
            return res.status(400).json({
                status: 'error',
                message: '주식 심볼이 필요합니다.',
            })
        }

        const response = await fastApiClient.get(
            `/api/realtime-price/${symbol}`
        )
        const stockData = response.data

        // 데이터 가공
        const formattedData = {
            symbol: stockData.symbol,
            name: stockData.name || '알 수 없음',
            price: {
                current: stockData.current_price,
                change: stockData.change,
                changePercent: stockData.change_percent,
                status:
                    stockData.change > 0
                        ? '상승'
                        : stockData.change < 0
                        ? '하락'
                        : '변동없음',
            },
            volume: stockData.volume,
            lastUpdate: stockData.timestamp,
            formattedPrice: new Intl.NumberFormat('ko-KR', {
                style: 'currency',
                currency: 'KRW',
            }).format(stockData.current_price),
        }

        res.json({
            status: 'success',
            data: formattedData,
        })
    } catch (error) {
        next(error)
    }
})

// 전고점 대비 하락 정보 조회
router.get('/peak-drop/:symbol', async (req, res, next) => {
    try {
        const { symbol } = req.params
        const { days } = req.query

        if (!symbol) {
            return res.status(400).json({
                status: 'error',
                message: '주식 심볼이 필요합니다.',
            })
        }

        const url = `/api/peak-drop/${symbol}${days ? `?days=${days}` : ''}`
        const response = await fastApiClient.get(url)
        const dropData = response.data

        // 데이터 가공
        const formattedData = {
            symbol: dropData.symbol,
            currentPrice: dropData.current_price,
            peakPrice: dropData.peak_price,
            drop: {
                value: dropData.drop_value,
                percent: dropData.drop_percent,
                significance:
                    dropData.drop_percent > 10
                        ? '유의미한 하락'
                        : '일반적인 변동',
            },
            peakDate: dropData.peak_date,
            analysis: generateDropAnalysis(dropData.drop_percent),
        }

        res.json({
            status: 'success',
            data: formattedData,
        })
    } catch (error) {
        next(error)
    }
})

// 하락률에 따른 분석 코멘트 생성 함수
function generateDropAnalysis(dropPercent) {
    if (dropPercent <= 0) {
        return '현재 전고점 대비 하락이 없습니다.'
    } else if (dropPercent < 5) {
        return '일반적인 시장 변동 범위 내 하락입니다.'
    } else if (dropPercent < 10) {
        return '소폭 조정 국면으로 관찰이 필요합니다.'
    } else if (dropPercent < 20) {
        return '의미있는 조정 국면입니다. 매수 기회를 검토해 볼 수 있습니다.'
    } else if (dropPercent < 30) {
        return '큰 폭의 하락이 진행 중입니다. 추가 하락 가능성에 주의하세요.'
    } else {
        return '매우 심각한 하락 국면입니다. 신중한 투자 결정이 필요합니다.'
    }
}

module.exports = router