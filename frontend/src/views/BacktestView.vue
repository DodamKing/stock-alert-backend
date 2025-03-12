<template>
    <div class="backtest-container">
        <h1>주식 백테스팅</h1>
        <p class="subtitle">과거 데이터를 기반으로 투자 전략을 테스트해보세요</p>

        <div class="feature-coming-soon">
            <div class="coming-soon-icon">🚧</div>
            <h2>준비 중입니다</h2>
            <p>곧 선보일 백테스팅 기능을 기대해주세요!</p>
            <router-link to="/" class="return-button">메인 페이지로 돌아가기</router-link>
        </div>

        <div class="feature-preview">
            <h3>다음 기능들을 제공할 예정입니다:</h3>
            <ul>
                <li>
                    <span class="feature-icon">📈</span>
                    <span class="feature-name">과거 주가 데이터 기반 시뮬레이션</span>
                </li>
                <li>
                    <span class="feature-icon">💼</span>
                    <span class="feature-name">다양한 투자 전략 테스트</span>
                </li>
                <li>
                    <span class="feature-icon">📊</span>
                    <span class="feature-name">수익률 분석 및 시각화</span>
                </li>
                <li>
                    <span class="feature-icon">⚙️</span>
                    <span class="feature-name">사용자 정의 매매 규칙 설정</span>
                </li>
            </ul>
        </div>
    </div>
</template>

<script>
export default {
    name: 'BacktestView'
}
</script>

<style scoped>
.backtest-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    color: var(--primary-color);
    text-align: center;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    color: var(--text-color);
    opacity: 0.7;
    margin-bottom: 30px;
}

.feature-coming-soon {
    background-color: var(--card-color);
    border-radius: 12px;
    padding: 40px 20px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    margin-bottom: 30px;
    border: 1px solid var(--border-color);
}

.coming-soon-icon {
    font-size: 4rem;
    margin-bottom: 20px;
}

.return-button {
    display: inline-block;
    background-color: var(--primary-color);
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    margin-top: 20px;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.3s;
}

.return-button:hover {
    background-color: var(--secondary-color);
    transform: translateY(-2px);
}

.feature-preview {
    background-color: var(--card-color);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    border: 1px solid var(--border-color);
}

.feature-preview h3 {
    margin-bottom: 20px;
    color: var(--primary-color);
}

.feature-preview ul {
    list-style: none;
    padding: 0;
}

.feature-preview li {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    padding: 10px;
    background-color: var(--background-color);
    border-radius: 8px;
    transition: transform 0.3s;
}

.feature-preview li:hover {
    transform: translateX(5px);
}

.feature-icon {
    font-size: 1.5rem;
    margin-right: 15px;
    display: inline-block;
    width: 30px;
}

.feature-name {
    font-weight: 500;
}

@media (max-width: 768px) {
    .backtest-container {
        padding: 10px;
    }
}
</style>