const express = require('express')
const helmet = require('helmet')
const cors = require('cors')
const morgan = require('morgan')
const config = require('./config/config')
const apiRoutes = require('./routes/api')

const app = express()
const PORT = config.port

app.use(helmet())
app.use(cors())
app.use(express.json())
app.use(express.urlencoded({ extended: true }))
app.use(morgan('dev'))
app.use('/api', config.apiLimiter)

app.use('/api', apiRoutes)

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