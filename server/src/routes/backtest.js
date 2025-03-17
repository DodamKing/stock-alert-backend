const router = require('express').Router()
const axios = require('axios')
const config = require('../config/config')

// FastAPI 클라이언트 (기존 클라이언트 재사용)
const fastApiClient = axios.create({
    baseURL: config.fastApiUrl,
    timeout: 60000, // 백테스팅은 시간이 더 걸릴 수 있으므로 60초로 설정
    headers: {
        'Content-Type': 'application/json',
    },
})

// 1. 여러 종목의 과거 가격 데이터 가져오기
router.get('/historical-prices', async (req, res, next) => {
    try {
        const { symbols, start_date, end_date, interval = '1d' } = req.query

        if (!symbols || !start_date) {
            return res.status(400).json({
                status: 'error',
                message: '종목 코드와 시작일은 필수입니다.',
            })
        }

        console.log(`과거 가격 데이터 요청: symbols=${symbols}, start_date=${start_date}, end_date=${end_date}, interval=${interval}`)

        // FastAPI에 요청
        let url = `/api/backtest/historical-prices?symbols=${encodeURIComponent(symbols)}&start_date=${encodeURIComponent(start_date)}`
        if (end_date) url += `&end_date=${encodeURIComponent(end_date)}`
        if (interval) url += `&interval=${encodeURIComponent(interval)}`

        console.log(`FastAPI 요청 URL: ${url}`)
        const response = await fastApiClient.get(url)

        // 데이터 가공 (필요한 경우)
        const priceData = response.data.data

        // 종목별 추가 정보 (예: 종목 유형 추가)
        Object.keys(priceData).forEach(symbol => {
            let stockType = 'stock'
            const market = priceData[symbol].market

            if (market && market.includes('KOSPI') || market && market.includes('KOSDAQ')) {
                stockType = 'kr-stock'
            } else if (market && market.includes('ETF')) {
                stockType = 'etf'
            } else if (market && (market.includes('NASDAQ') || market.includes('NYSE') || market.includes('AMEX'))) {
                stockType = 'us-stock'
            }

            priceData[symbol].type = stockType
        })

        res.json({
            status: 'success',
            data: priceData,
            symbols_requested: response.data.symbols_requested,
            symbols_found: response.data.symbols_found
        })
    } catch (error) {
        console.error('과거 가격 데이터 API 오류:', error)
        // 에러 응답이 있으면 그 내용을 전달
        if (error.response && error.response.data) {
            return res.status(error.response.status || 500).json({
                status: 'error',
                message: error.response.data.detail || '과거 가격 데이터를 가져오는 중 오류가 발생했습니다.',
            })
        }
        next(error)
    }
})

// 2. 적립식 투자 백테스팅 API
router.post('/dca', async (req, res, next) => {
    try {
        const backtestParams = req.body

        if (!backtestParams.symbols || !backtestParams.allocation || !backtestParams.start_date) {
            return res.status(400).json({
                status: 'error',
                message: '종목 코드, 투자 비중, 시작일은 필수입니다.',
            })
        }

        // 시장 그룹 및 통화 확인 (프론트엔드에서 제공)
        const marketGroup = backtestParams.market_group || 'kr' // 기본값은 한국
        const currency = backtestParams.currency || 'KRW'

        console.log(`적립식 투자 백테스팅 요청: symbols=${backtestParams.symbols}, start_date=${backtestParams.start_date}, market_group=${marketGroup}`)

        // FastAPI에 요청
        const response = await fastApiClient.post('/api/backtest/dca', backtestParams)

        // 결과 가공 및 보강
        const backtestResult = response.data.data

        // 종목 유형 정보 추가 및 기타 가공
        if (backtestResult && backtestResult.portfolio && backtestResult.portfolio.length > 0) {
            // 총 포트폴리오 가치 계산
            const totalValue = backtestResult.portfolio.reduce((sum, item) => sum + item.current_value, 0);

            // 각 종목의 비중을 재계산 (현금 포함)
            backtestResult.portfolio = backtestResult.portfolio.map(item => {
                let stockType = 'stock';
                const symbol = item.symbol;

                // 현금 항목 특별 처리
                if (symbol === 'CASH') {
                    return {
                        ...item,
                        type: 'cash',
                        weight: totalValue > 0 ? (item.current_value / totalValue * 100) : 0
                    };
                }

                // 시장 그룹에 따른 종목 타입 추정
                if (marketGroup === 'kr') {
                    // 한국 주식/ETF 패턴
                    if (symbol.match(/^(A)?[0-9]{6}$/)) {
                        if (symbol.includes('ETF') || item.name?.includes('ETF')) {
                            stockType = 'etf';
                        } else {
                            stockType = 'kr-stock';
                        }
                    }
                } else if (marketGroup === 'us') {
                    // 미국 주식/ETF 패턴
                    if (symbol.match(/^[A-Z]{1,5}$/)) {
                        if (symbol.includes('ETF') || item.name?.includes('ETF')) {
                            stockType = 'etf';
                        } else {
                            stockType = 'us-stock';
                        }
                    }
                }

                // 비중 재계산 (현재 가치 ÷ 총 가치 × 100)
                const weight = totalValue > 0 ? (item.current_value / totalValue * 100) : 0;

                return {
                    ...item,
                    type: stockType,
                    weight: weight, // 비중 재계산하여 덮어쓰기
                    shares: Math.floor(item.shares) // 주식 수량 정수로 표시
                };
            });
        }

        // 추가 분석 정보
        const summary = backtestResult.summary
        if (summary) {
            // 투자 성과 점수 (0-100) 계산
            const performanceScore = calculatePerformanceScore(summary.cagr, summary.total_profit_pct)

            // CAGR 범주화 (이미 백엔드에서 제공하는 경우 사용)
            let cagr_rating = summary.cagr_rating || 'Not rated'
            if (!summary.cagr_rating) {
                if (summary.cagr < 0) cagr_rating = '손실'
                else if (summary.cagr < 5) cagr_rating = '낮음'
                else if (summary.cagr < 10) cagr_rating = '보통'
                else if (summary.cagr < 15) cagr_rating = '좋음'
                else cagr_rating = '탁월함'
            }

            // 현금 잔액 확인 (백엔드에서 제공하는 경우 사용)
            const cashBalance = summary.cash_balance || 0

            // 요약 정보에 추가
            backtestResult.summary.performance_score = summary.performance_score || performanceScore
            backtestResult.summary.cagr_rating = cagr_rating
            backtestResult.summary.cash_balance = cashBalance

            // 시장 그룹 및 통화 정보 추가
            backtestResult.summary.market_group = marketGroup
            backtestResult.summary.currency = currency

            // 벤치마크와의 비교 코멘트
            backtestResult.analysis = {
                comment: generateBacktestAnalysisComment(summary, marketGroup),
                key_metrics: [
                    {
                        name: '연평균 수익률(CAGR)',
                        value: `${summary.cagr.toFixed(2)}%`,
                        rating: cagr_rating
                    },
                    {
                        name: '총 수익률',
                        value: `${summary.total_profit_pct.toFixed(2)}%`,
                        rating: summary.total_profit_pct > 0 ? '이익' : '손실'
                    },
                    {
                        name: '투자 기간',
                        value: `${summary.investment_period.years.toFixed(1)}년`,
                        rating: 'N/A'
                    }
                ]
            }

            // 현금 정보가 있으면 지표에 추가
            if (cashBalance > 0) {
                backtestResult.analysis.key_metrics.push({
                    name: '남은 현금',
                    value: formatCurrency(cashBalance, currency),
                    rating: 'N/A'
                });
            }
        }

        res.json({
            status: 'success',
            data: backtestResult
        })
    } catch (error) {
        console.error('적립식 투자 백테스팅 API 오류:', error)
        // 에러 응답이 있으면 그 내용을 전달
        if (error.response && error.response.data) {
            return res.status(error.response.status || 500).json({
                status: 'error',
                message: error.response.data.detail || '백테스팅 중 오류가 발생했습니다.',
            })
        }
        next(error)
    }
})

// 3. 백테스팅 파라미터 검증 API
router.post('/validate', async (req, res) => {
    const { symbols, allocation, start_date, end_date } = req.body

    const errors = []

    // 필수 필드 검증
    if (!symbols || !Array.isArray(symbols) || symbols.length === 0) {
        errors.push('최소 1개 이상의 종목을 선택해야 합니다.')
    }

    if (!allocation || typeof allocation !== 'object') {
        errors.push('각 종목별 투자 비중을 설정해야 합니다.')
    } else {
        // 투자 비중 합계 검증
        const totalAllocation = Object.values(allocation).reduce((sum, value) => sum + parseFloat(value), 0)
        if (Math.abs(totalAllocation - 100) > 0.1) { // 0.1% 오차 허용
            errors.push(`투자 비중의 합계는 100%여야 합니다. (현재: ${totalAllocation.toFixed(1)}%)`)
        }
    }

    if (!start_date) {
        errors.push('시작일은 필수입니다.')
    } else {
        // 유효한 날짜 형식인지 검증
        if (!/^\d{4}-\d{2}-\d{2}$/.test(start_date)) {
            errors.push('시작일은 YYYY-MM-DD 형식이어야 합니다.')
        }
    }

    if (end_date && !/^\d{4}-\d{2}-\d{2}$/.test(end_date)) {
        errors.push('종료일은 YYYY-MM-DD 형식이어야 합니다.')
    }

    // 시작일이 종료일보다 이후인지 검증
    if (start_date && end_date && new Date(start_date) > new Date(end_date)) {
        errors.push('시작일은 종료일보다 이전이어야 합니다.')
    }

    if (errors.length > 0) {
        return res.json({
            status: 'error',
            valid: false,
            errors: errors
        })
    }

    res.json({
        status: 'success',
        valid: true
    })
})

// 투자 성과 점수 계산 함수 (0-100)
function calculatePerformanceScore(cagr, totalProfitPct) {
    if (cagr === undefined || totalProfitPct === undefined) return 50

    // CAGR 기반 기본 점수 (0-80)
    let score = 0
    if (cagr < 0) {
        // 음수 CAGR은 낮은 점수
        score = Math.max(0, 40 + cagr * 4) // 예: -10% CAGR -> 0점
    } else {
        // 양수 CAGR은 높은 점수
        score = Math.min(80, 40 + cagr * 4) // 예: 10% CAGR -> 80점
    }

    // 총 수익률로 추가 점수 (0-20)
    const profitBonus = Math.min(20, Math.max(0, totalProfitPct / 10))

    return Math.round(score + profitBonus)
}

// 백테스팅 분석 코멘트 생성 함수
function generateBacktestAnalysisComment(summary) {
    const { cagr, total_profit_pct, investment_period } = summary

    // 기본 코멘트
    let comment = `${investment_period.years.toFixed(1)}년 동안의 적립식 투자 시뮬레이션 결과, `

    // 수익률에 따른 코멘트
    if (total_profit_pct > 50) {
        comment += `총 ${total_profit_pct.toFixed(1)}%의 높은 수익률을 기록했습니다. `
    } else if (total_profit_pct > 20) {
        comment += `총 ${total_profit_pct.toFixed(1)}%의 양호한 수익률을 기록했습니다. `
    } else if (total_profit_pct > 0) {
        comment += `총 ${total_profit_pct.toFixed(1)}%의 소폭 수익을 기록했습니다. `
    } else {
        comment += `총 ${Math.abs(total_profit_pct).toFixed(1)}%의 손실이 발생했습니다. `
    }

    // CAGR에 따른 코멘트
    if (cagr > 15) {
        comment += `연평균 수익률(CAGR)은 ${cagr.toFixed(1)}%로 매우 우수합니다.`
    } else if (cagr > 10) {
        comment += `연평균 수익률(CAGR)은 ${cagr.toFixed(1)}%로 양호한 성과입니다.`
    } else if (cagr > 5) {
        comment += `연평균 수익률(CAGR)은 ${cagr.toFixed(1)}%로 적정한 수준입니다.`
    } else if (cagr > 0) {
        comment += `연평균 수익률(CAGR)은 ${cagr.toFixed(1)}%로 다소 낮은 수준입니다.`
    } else {
        comment += `연평균 수익률(CAGR)은 ${cagr.toFixed(1)}%로 손실이 발생했습니다.`
    }

    return comment
}

// 숫자 포맷팅 함수
function formatNumber(num) {
    return new Intl.NumberFormat().format(Math.round(num));
}

// 통화 포맷팅 함수
function formatCurrency(amount, currency) {
    if (currency === 'USD') {
        return '$' + new Intl.NumberFormat('en-US').format(Math.round(amount));
    } else {
        return new Intl.NumberFormat('ko-KR').format(Math.round(amount)) + '원';
    }
}

module.exports = router