// server/src/service/marketService.js
const axios = require('axios');
const fs = require('fs/promises');
const path = require('path');

// FastAPI 서버 URL
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

// 데이터를 저장할 디렉토리
const DATA_DIR = path.join(__dirname, '../../data');

// 가져올 시장 코드 목록
const MARKET_CODES = require('../config/market_codes')

/**
 * 특정 시장의 종목 목록을 가져옵니다.
 */
async function fetchMarketSymbols(marketCode) {
    try {
        console.log(`${marketCode} 시장 데이터 가져오는 중...`);
        const response = await axios.get(`${FASTAPI_URL}/api/market-symbols/${marketCode}`);
        return response.data;
    } catch (error) {
        console.error(`${marketCode} 시장 종목 가져오기 실패:`, error.message);
        throw error;
    }
}

/**
 * 데이터 디렉토리가 없으면 생성합니다.
 */
async function ensureDataDir() {
    try {
        await fs.mkdir(DATA_DIR, { recursive: true });
    } catch (error) {
        console.error('데이터 디렉토리 생성 실패:', error.message);
        throw error;
    }
}

/**
 * 모든 시장의 종목 정보를 가져와 JSON 파일로 저장합니다.
 */
async function fetchAndStoreMarketData() {
    try {
        console.log('시장 데이터 업데이트 시작');

        // 데이터 디렉토리 확인
        await ensureDataDir();

        // 각 시장별 종목 정보 가져오기
        for (const marketCode of MARKET_CODES) {
            try {
                // 시장 데이터 가져오기
                const marketData = await fetchMarketSymbols(marketCode);

                // 개별 시장 데이터를 파일로 저장
                const filePath = path.join(DATA_DIR, `${marketCode}.json`);
                await fs.writeFile(
                    filePath,
                    JSON.stringify(marketData, null, 2),
                    'utf8'
                );

                console.log(`${marketCode} 시장 종목 ${marketData.stocks.length}개 저장 완료`);
            } catch (error) {
                console.error(`${marketCode} 시장 데이터 처리 중 오류:`, error.message);
                // 하나의 시장에서 오류가 발생해도 계속 진행
                continue;
            }
        }

        // 마지막 업데이트 시간 저장
        await fs.writeFile(
            path.join(DATA_DIR, 'last_update.json'),
            JSON.stringify({ lastUpdate: new Date().toISOString() }, null, 2),
            'utf8'
        );

        console.log('모든 시장 데이터 업데이트 완료');

        return { success: true, message: '시장 데이터 업데이트 성공' };
    } catch (error) {
        console.error('시장 데이터 업데이트 실패:', error.message);
        return { success: false, error: error.message };
    }
}

// 직접 실행되었을 때 작업 수행
if (require.main === module) {
    fetchAndStoreMarketData()
        .then(result => {
            console.log(result);
            process.exit(0);
        })
        .catch(error => {
            console.error('데이터 가져오기 작업 실패:', error);
            process.exit(1);
        });
}

module.exports = { fetchAndStoreMarketData };