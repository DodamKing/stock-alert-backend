const express = require('express')
const helmet = require('helmet')
const cors = require('cors')
const path = require('path')
const morgan = require('morgan')
const config = require('./config/config')
const apiRoutes = require('./routes/api')
const backtestRoutes = require('./routes/backtest')

const app = express()
const PORT = config.port

app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            ...helmet.contentSecurityPolicy.getDefaultDirectives(),
            "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            "img-src": ["'self'", "data:"]
        }
    }
}))
app.use(cors())
app.use(express.json())
app.use(express.urlencoded({ extended: true }))
app.use(morgan('dev'))
app.use('/api', config.apiLimiter)

// const refererCheckMiddleware = require('./middlewares/refererCheck')
// app.use('/api', refererCheckMiddleware, apiRoutes)
// 일단 referer 없이 해보자
app.use('/api', apiRoutes)
app.use('/api/backtest', backtestRoutes)

app.use(express.static(path.join(__dirname, '../../frontend/dist')))

// SPA 라우팅을 위해 모든 요청을 index.html로 리다이렉트
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../../frontend/dist/index.html'))
})

// 에러 핸들러
app.use((err, req, res, next) => {
    const statusCode = err.status || 500
    console.error(`[에러] ${statusCode} - ${err.message}`)

    res.status(statusCode).json({
        status: 'error',
        statusCode,
        message: err.message,
        stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
    })
})

// 서버 시작
const server = app.listen(PORT, () => {
    console.log(`🚀 Express 서버가 ${PORT} 포트에서 실행 중입니다.`)
    console.log(`🔄 FastAPI 서버 연결: ${config.fastApiUrl}`)
    console.log(`🛠️ 환경: ${config.env}`)

    require('./config/setupCron')
})

// 프로세스 종료 처리
process.on('SIGTERM', () => {
    console.log('SIGTERM 신호 수신, 서버 종료')
    server.close(() => {
        console.log('서버가 정상적으로 종료되었습니다.')
        process.exit(0)
    })
})

process.on('SIGINT', () => {
    console.log('SIGINT 신호 수신, 서버 종료')
    server.close(() => {
        console.log('서버가 정상적으로 종료되었습니다.')
        process.exit(0)
    })
})

// 처리되지 않은 예외 처리
process.on('uncaughtException', (err) => {
    console.error('처리되지 않은 예외:', err)
    server.close(() => {
        process.exit(1)
    })
})

process.on('unhandledRejection', (reason) => {
    console.error('처리되지 않은 프라미스 거부:', reason)
})