<!-- views/BacktestView.vue -->
<template>
    <div class="backtest-container">
        <h1>주식 백테스팅</h1>
        <p class="subtitle">과거 데이터를 기반으로 투자 전략을 테스트해보세요</p>

        <!-- 백테스팅 유형 선택 탭 -->
        <div class="backtest-tabs">
            <button v-for="(tab, index) in backtestTypes" :key="index" :class="{ active: selectedTab === index }"
                @click="selectTab(index)">
                {{ tab.name }}
            </button>
        </div>

        <!-- 적립식 투자 시뮬레이션 탭 -->
        <div v-if="selectedTab === 0" class="tab-content">
            <DCABacktest />
        </div>

        <!-- 다른 전략 준비 중 탭 -->
        <div v-else class="tab-content">
            <div class="feature-coming-soon">
                <div class="coming-soon-icon">🚧</div>
                <h2>준비 중입니다</h2>
                <p>{{ backtestTypes[selectedTab].name }} 기능을 곧 선보일 예정입니다!</p>
            </div>

            <div class="feature-preview">
                <h3>다음 기능들을 제공할 예정입니다:</h3>
                <ul>
                    <li v-for="(feature, index) in backtestTypes[selectedTab].features" :key="index">
                        <span class="feature-icon">{{ feature.icon }}</span>
                        <span class="feature-name">{{ feature.name }}</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
import DCABacktest from '../components/DCABacktest.vue';

export default {
    name: 'BacktestView',
    components: {
        DCABacktest
    },
    data() {
        return {
            selectedTab: 0, // 기본 탭: 적립식 투자
            backtestTypes: [
                {
                    name: '적립식 투자 시뮬레이션',
                    description: '정기적으로 투자했을 때의 수익률을 시뮬레이션합니다.',
                    features: [
                        { icon: '📈', name: '주기적 투자 시뮬레이션' },
                        { icon: '💰', name: '복리 효과 분석' },
                        { icon: '📊', name: '포트폴리오 구성 최적화' }
                    ]
                },
                {
                    name: '변동성 기반 투자',
                    description: '시장 변동성에 기반한 투자 전략을 테스트합니다.',
                    features: [
                        { icon: '📉', name: '하락률 기반 매수 전략' },
                        { icon: '📊', name: '변동성 분석 및 시각화' },
                        { icon: '⚖️', name: '리스크 관리 시뮬레이션' }
                    ]
                },
                {
                    name: '기술적 지표 기반 백테스팅',
                    description: '이동평균선, RSI 등 기술적 지표 기반 전략을 테스트합니다.',
                    features: [
                        { icon: '📊', name: '다양한 기술적 지표 적용' },
                        { icon: '🔄', name: '매매 신호 자동 감지' },
                        { icon: '📈', name: '백테스팅 결과 상세 분석' }
                    ]
                }
            ]
        };
    },
    methods: {
        selectTab(index) {
            this.selectedTab = index;
        }
    }
};
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

.backtest-tabs {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    overflow-x: auto;
    padding-bottom: 5px;
}

.backtest-tabs button {
    padding: 10px 20px;
    background-color: var(--card-color);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.3s;
    color: var(--text-color);
}

.backtest-tabs button.active {
    background-color: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.tab-content {
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

    .backtest-tabs {
        gap: 5px;
    }

    .backtest-tabs button {
        padding: 8px 15px;
        font-size: 0.9rem;
    }
}
</style>