<!-- StockDropInfo.vue -->
<template>
    <div class="stock-drop-info-component" :class="getDropClass(stockData.drop.percent)">
        <div class="drop-header">
            <div class="drop-title">전고점 대비 하락</div>
            <div class="drop-significance">{{ stockData.drop.significance }}</div>
        </div>
        <div class="drop-values">
            <div class="drop-percent">{{ stockData.drop.percent.toFixed(2) }}%</div>
            <div class="drop-value">{{ formatPrice(stockData.drop.value) }}</div>
        </div>
        <div class="drop-bar-container">
            <div class="drop-bar-bg"></div>
            <div class="drop-bar" :style="{ width: '0%' }" ref="dropBar"></div>
        </div>
        <div class="drop-analysis">{{ stockData.analysis }}</div>

        <div class="notify-container">
            <div class="feature-coming-soon">
                <div class="coming-soon-icon">🔔</div>
                <h4>알림 기능 개발 중</h4>
                <p>이 종목의 하락률 변화를 알림으로 받는 기능이 곧 제공될 예정입니다.</p>
            </div>
            <!-- 비활성화된 버튼 -->
            <button class="notify-btn disabled" disabled>
                <span>이 종목 알림 받기</span>
                <span class="coming-soon-badge">개발 중</span>
            </button>
            <!-- <button @click="setNotification" class="notify-btn">
                <span v-if="hasNotification">알림 설정됨 ✓</span>
                <span v-else>이 종목 알림 받기</span>
            </button>
            <div v-if="showNotifyOptions" class="notify-options">
                <p>하락률이 다음 수준에 도달하면 알림 받기:</p>
                <select v-model="notifyThreshold">
                    <option value="5">5% 이상</option>
                    <option value="10">10% 이상</option>
                    <option value="15">15% 이상</option>
                    <option value="20">20% 이상</option>
                    <option value="25">25% 이상</option>
                    <option value="30">30% 이상</option>
                </select>
                <button @click="saveNotification" class="save-notify-btn">저장</button>
            </div> -->
        </div>
    </div>
</template>

<script>
export default {
    name: 'StockDropInfo',
    props: {
        stockData: {
            type: Object,
            required: true
        },
        hasNotification: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            showNotifyOptions: false,
            notifyThreshold: 20,
            isMobile: false
        };
    },
    mounted() {
        // dropBar 애니메이션 설정
        this.$nextTick(() => {
            if (this.$refs.dropBar) {
                setTimeout(() => {
                    this.$refs.dropBar.style.width = Math.min(this.stockData.drop.percent, 100) + '%';
                }, 100);
            }
        });

        // 디바이스 타입 확인
        this.checkDeviceType();
        window.addEventListener('resize', this.checkDeviceType);
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.checkDeviceType);
    },
    methods: {
        formatPrice(price) {
            return new Intl.NumberFormat('ko-KR', {
                maximumFractionDigits: 0
            }).format(price);
        },
        getDropClass(dropPercent) {
            if (dropPercent <= 0) return 'no-drop';
            if (dropPercent < 5) return 'minor-drop';
            if (dropPercent < 10) return 'small-drop';
            if (dropPercent < 20) return 'medium-drop';
            if (dropPercent < 30) return 'large-drop';
            return 'severe-drop';
        },
        // setNotification() {
        //     if (this.hasNotification) {
        //         // 이미 설정된 알림이 있으면 제거 요청
        //         this.$emit('remove-notification', this.stockData.symbol);
        //     } else {
        //         // 알림 설정 옵션 표시
        //         this.showNotifyOptions = !this.showNotifyOptions;
        //     }
        // },
        // saveNotification() {
        //     // 저장 이벤트 발행
        //     this.$emit('save-notification', {
        //         symbol: this.stockData.symbol,
        //         threshold: this.notifyThreshold
        //     });

        //     this.showNotifyOptions = false;
        // },
        checkDeviceType() {
            this.isMobile = window.innerWidth <= 768;
        }
    }
};
</script>

<style scoped>
.stock-drop-info-component {
    background-color: var(--background-color);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
    border: 1px solid var(--border-color);
}

.drop-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.drop-title {
    font-weight: 600;
    font-size: 1.1rem;
}

.drop-significance {
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    color: white;
}

.drop-values {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    align-items: flex-end;
}

.drop-percent {
    font-size: 2.2rem;
    font-weight: 700;
}

.drop-value {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-color);
    opacity: 0.7;
}

.drop-bar-container {
    height: 10px;
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 5px;
    overflow: hidden;
    margin-bottom: 15px;
    position: relative;
}

.drop-bar-bg {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    opacity: 0.1;
}

.drop-bar {
    height: 100%;
    border-radius: 5px;
    transition: width 1.2s cubic-bezier(0.22, 1, 0.36, 1);
}

.drop-analysis {
    font-size: 1.1rem;
    line-height: 1.5;
    margin-top: 20px;
    padding: 15px;
    background-color: var(--card-color);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.notify-container {
    margin-top: 20px;
    padding: 15px;
    background-color: var(--card-color);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.notify-btn {
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 15px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s;
    width: 100%;
    min-height: 44px;
    /* 모바일 터치 최적화 */
}

.notify-btn:hover {
    background-color: var(--secondary-color);
    transform: translateY(-2px);
}

.notify-options {
    margin-top: 15px;
    padding: 15px;
    background-color: var(--background-color);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    animation: fadeIn 0.3s ease-out;
}

.notify-options p {
    margin-bottom: 10px;
}

.notify-options select {
    width: 100%;
    padding: 10px;
    margin: 10px 0;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    background-color: var(--card-color);
    color: var(--text-color);
    font-size: 1rem;
    height: 44px;
    /* 모바일 터치 최적화 */
}

.save-notify-btn {
    background-color: var(--accent-color);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 15px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s;
    width: 100%;
    min-height: 44px;
    /* 모바일 터치 최적화 */
}

.save-notify-btn:hover {
    background-color: #ea580c;
}

/* 드롭 클래스 스타일 */
.no-drop {
    border-left: 5px solid var(--no-drop-color);
}

.no-drop .drop-significance,
.no-drop .drop-bar {
    background-color: var(--no-drop-color);
}

.no-drop .drop-bar-bg {
    background-color: var(--no-drop-color);
}

.minor-drop {
    border-left: 5px solid var(--minor-drop-color);
}

.minor-drop .drop-significance,
.minor-drop .drop-bar {
    background-color: var(--minor-drop-color);
}

.minor-drop .drop-bar-bg {
    background-color: var(--minor-drop-color);
}

.small-drop {
    border-left: 5px solid var(--small-drop-color);
}

.small-drop .drop-significance,
.small-drop .drop-bar {
    background-color: var(--small-drop-color);
}

.small-drop .drop-bar-bg {
    background-color: var(--small-drop-color);
}

.medium-drop {
    border-left: 5px solid var(--medium-drop-color);
}

.medium-drop .drop-significance,
.medium-drop .drop-bar {
    background-color: var(--medium-drop-color);
}

.medium-drop .drop-bar-bg {
    background-color: var(--medium-drop-color);
}

.large-drop {
    border-left: 5px solid var(--large-drop-color);
}

.large-drop .drop-significance,
.large-drop .drop-bar {
    background-color: var(--large-drop-color);
}

.large-drop .drop-bar-bg {
    background-color: var(--large-drop-color);
}

.severe-drop {
    border-left: 5px solid var(--severe-drop-color);
}

.severe-drop .drop-significance,
.severe-drop .drop-bar {
    background-color: var(--severe-drop-color);
}

.severe-drop .drop-bar-bg {
    background-color: var(--severe-drop-color);
}

/* 모바일 최적화 */
@media (max-width: 768px) {
    .stock-drop-info-component {
        padding: 15px;
        margin-bottom: 20px;
    }

    .drop-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .drop-title {
        font-size: 1rem;
    }

    .drop-significance {
        padding: 4px 10px;
        font-size: 0.8rem;
    }

    .drop-values {
        flex-direction: column;
        align-items: flex-start;
        gap: 5px;
    }

    .drop-percent {
        font-size: 1.8rem;
    }

    .drop-value {
        font-size: 1rem;
    }

    .drop-analysis {
        font-size: 0.95rem;
        padding: 12px;
        margin-top: 15px;
    }

    .notify-container {
        padding: 12px;
        margin-top: 15px;
    }

    .notify-btn,
    .save-notify-btn {
        padding: 10px;
    }

    .notify-options {
        padding: 12px;
    }

    .notify-options p {
        font-size: 0.9rem;
    }

    /* 터치 피드백 개선 */
    .notify-btn:active,
    .save-notify-btn:active {
        opacity: 0.8;
        transform: scale(0.98);
    }
}

/* 작은 모바일 화면 */
@media (max-width: 480px) {
    .stock-drop-info-component {
        padding: 12px;
    }

    .drop-percent {
        font-size: 1.6rem;
    }

    .drop-analysis {
        font-size: 0.9rem;
        padding: 10px;
    }

    .notify-container,
    .notify-options {
        padding: 10px;
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 모바일 터치 최적화 - hover 대신 active 사용 */
@media (hover: none) {

    .notify-btn:hover,
    .save-notify-btn:hover {
        transform: none;
    }
}

/* 준비 중 기능 알림 */
.feature-coming-soon {
    background-color: var(--background-color);
    border: 1px dashed var(--border-color);
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    margin-bottom: 15px;
}

.coming-soon-icon {
    font-size: 2rem;
    margin-bottom: 10px;
    animation: pulse 2s infinite;
}

.feature-coming-soon h4 {
    margin: 5px 0;
    color: var(--primary-color);
}

.feature-coming-soon p {
    margin: 10px 0 5px;
    font-size: 0.9rem;
    line-height: 1.5;
    color: var(--text-color);
    opacity: 0.8;
}

/* 비활성화된 버튼 */
.notify-btn.disabled {
    background-color: #ccc;
    cursor: not-allowed;
    position: relative;
    overflow: hidden;
}

.notify-btn.disabled:hover {
    transform: none;
    background-color: #ccc;
}

.coming-soon-badge {
    position: absolute;
    top: -8px;
    right: -25px;
    background-color: var(--accent-color);
    color: white;
    font-size: 0.7rem;
    padding: 2px 20px;
    transform: rotate(45deg);
}

@keyframes pulse {
    0% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.1);
    }

    100% {
        transform: scale(1);
    }
}

/* 모바일 최적화 */
@media (max-width: 768px) {
    .feature-coming-soon {
        padding: 12px;
    }

    .coming-soon-icon {
        font-size: 1.5rem;
    }

    .feature-coming-soon h4 {
        font-size: 1rem;
    }

    .feature-coming-soon p {
        font-size: 0.8rem;
    }
}
</style>