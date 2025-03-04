// config.js
require('dotenv').config()
const rateLimit = require('express-rate-limit')

const config = {
    // 서버 설정
    port: process.env.PORT || 3000,
    env: process.env.NODE_ENV || 'development',

    // FastAPI 연결 설정
    fastApiUrl: process.env.FASTAPI_URL || 'http://localhost:8000',

    // Rate Limit 설정
    rateLimit: {
        windowMs: 15 * 60 * 1000, // 15분
        max: 100, // IP당 15분 내 최대 100 요청,
        message: '너무 많은 요청을 보냈습니다. 15분 후에 다시 시도해주세요.'
    },

    apiLimiter : rateLimit({
        windowMs: 15 * 60 * 1000, // 15분
        max: 100, // IP당 15분 내 최대 100 요청,
        message: '너무 많은 요청을 보냈습니다. 15분 후에 다시 시도해주세요.'
    })
}

module.exports = config
