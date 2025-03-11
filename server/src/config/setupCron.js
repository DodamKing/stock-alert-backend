// server/src/config/setupCron.js
const cron = require('node-cron');
const { fetchAndStoreMarketData } = require('../services/marketService');

// 매일 오전 5시에 실행 (거래 시작 전 최신 데이터로 업데이트)
cron.schedule('0 5 * * *', async () => {
    console.log('시장 데이터 업데이트 cron 작업 시작 -', new Date().toISOString());

    try {
        const result = await fetchAndStoreMarketData();
        if (result.success) {
            console.log('시장 데이터 업데이트 cron 작업 성공');
        } else {
            console.error('시장 데이터 업데이트 cron 작업 실패:', result.error);
        }
    } catch (error) {
        console.error('시장 데이터 업데이트 cron 작업 예외 발생:', error);
    }
}, {
    scheduled: true,
    timezone: "Asia/Seoul" // 한국 시간 기준
});

console.log('시장 데이터 cron 작업 설정 완료 - 매일 오전 5시(KST)에 실행됩니다.');