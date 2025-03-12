const refererCheckMiddleware = (req, res, next) => {
    const referer = req.headers.referer || req.headers.referrer;

    // API 직접 호출 감지 (리퍼러가 없는 경우)
    if (!referer) {
        console.log('referer 없음!');
        return res.status(403).json({
            status: 'error',
            message: '직접적인 API 접근은 허용되지 않습니다.'
        });
    }

    // 개발 환경에서 허용되는 리퍼러 목록
    const devAllowedReferers = ['http://localhost:', 'http://127.0.0.1:'];

    // 프로덕션 환경에서 허용되는 리퍼러 목록 (나중에 도메인이 확정되면 추가)
    const prodAllowedReferers = ['https://yourdomain.com', 'https://www.yourdomain.com'];

    const allowedReferers =
        process.env.NODE_ENV === 'production' ? prodAllowedReferers : devAllowedReferers;

    // 어떤 허용된 리퍼러와도 일치하지 않으면 거부
    const isAllowed = allowedReferers.some(allowed => referer.includes(allowed));

    if (!isAllowed) {
        console.log('허가되지 않은 출처');
        return res.status(403).json({
            status: 'error',
            message: '허가되지 않은 출처의 요청입니다.'
        });
    }

    next();
};

module.exports = refererCheckMiddleware