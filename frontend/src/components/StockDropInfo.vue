<!-- StockDropInfo.vue -->
<template>
    <div class="drop-container" :class="getDropClass(stockData.drop.percent)">
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
            <button @click="setNotification" class="notify-btn">
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
            </div>
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
            notifyThreshold: 20
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
        setNotification() {
            if (this.hasNotification) {
                // 이미 설정된 알림이 있으면 제거 요청
                this.$emit('remove-notification', this.stockData.symbol);
            } else {
                // 알림 설정 옵션 표시
                this.showNotifyOptions = !this.showNotifyOptions;
            }
        },
        saveNotification() {
            // 저장 이벤트 발행
            this.$emit('save-notification', {
                symbol: this.stockData.symbol,
                threshold: this.notifyThreshold
            });

            this.showNotifyOptions = false;
        }
    }
};
</script>