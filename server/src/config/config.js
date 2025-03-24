// config.js
require('dotenv').config()
const rateLimit = require('express-rate-limit')
const helmet = require('helmet')

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
    }),

    contentSecurityPolicy: {
        directives: {
            ...helmet.contentSecurityPolicy.getDefaultDirectives(),
            "default-src": ["'self'"],
            "script-src": [
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",
                "https://pagead2.googlesyndication.com",
                "https://*.googleadservices.com",
                "https://*.google-analytics.com",
                "https://adservice.google.com",
                "https://*.adtrafficquality.google",
                "https://fundingchoicesmessages.google.com" 
            ],
            "frame-src": [
                "'self'",
                "https://googleads.g.doubleclick.net",
                "https://*.googlesyndication.com",
                "https://tpc.googlesyndication.com",
                "https://*.adtrafficquality.google",
                "https://www.google.com",
                "https://fundingchoicesmessages.google.com"
            ],
            "img-src": [
                "'self'",
                "data:",
                "blob:",  // blob URL도 추가
                "https://*.google-analytics.com",
                "https://*.googleadservices.com",
                "https://*.googlesyndication.com",
                "https://googleads.g.doubleclick.net",
                "https://*.adtrafficquality.google"  // 추가
            ],
            "connect-src": [
                "'self'",
                "https://adservice.google.com",
                "https://*.googlesyndication.com",
                "https://*.g.doubleclick.net",
                "https://*.adtrafficquality.google",
                "https://*.google-analytics.com",
                "https://fundingchoicesmessages.google.com"
            ],
            "style-src": [
                "'self'",
                "'unsafe-inline'",
                "https://fonts.googleapis.com"
            ],
            "font-src": [
                "'self'",
                "https://fonts.gstatic.com"
            ]
        }
    }
}

module.exports = config
