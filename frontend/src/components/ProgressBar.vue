<!-- components/ProgressBar.vue -->
<template>
    <div class="progress-component">
        <div class="progress-container">
            <div class="progress-bar" :style="{ width: `${value}%` }"></div>
        </div>

        <div class="progress-info" v-if="showInfo">
            <span>{{ Math.round(value) }}% 완료</span>
            <span v-if="showTime">예상 소요 시간: {{ remainingTimeText }}</span>
        </div>

        <div class="progress-message" v-if="message">
            {{ message }}
        </div>
    </div>
</template>

<script>
export default {
    name: 'ProgressBar',
    props: {
        value: {
            type: Number,
            default: 0,
            validator: (val) => val >= 0 && val <= 100
        },
        showInfo: {
            type: Boolean,
            default: true
        },
        showTime: {
            type: Boolean,
            default: true
        },
        message: {
            type: String,
            default: ''
        },
        startTime: {
            type: Number,
            default: null
        },
        estimatedTime: {
            type: Number,
            default: 0
        }
    },
    data() {
        return {
            lastUpdated: Date.now()
        };
    },
    computed: {
        remainingTimeText() {
            if (!this.startTime) return "계산 중...";

            const elapsed = (Date.now() - this.startTime) / 1000;

            // 남은 시간을 더 정확하게 계산
            // 1. 이미 완료된 비율 계산
            const completedRatio = Math.max(0, Math.min((this.value - 10) / 85, 0.95));

            // 2. 진행 상태가 10% 미만이면 초기 추정 사용
            if (completedRatio <= 0) {
                return `약 ${Math.ceil(this.estimatedTime)}초`;
            }

            // 3. 남은 비율 계산
            const remainingRatio = 1 - completedRatio;

            // 4. 실제 경과 시간 기반으로 남은 시간 추정
            const estimatedRemaining = Math.max(0, elapsed * (remainingRatio / completedRatio));

            if (estimatedRemaining <= 0) return "곧 완료됩니다...";
            if (estimatedRemaining < 60) return `${Math.ceil(estimatedRemaining)}초`;
            return `약 ${Math.ceil(estimatedRemaining / 60)}분`;
        }
    },
    watch: {
        // 진행률 변화에 따라 lastUpdated 갱신 (강제 렌더링 용도)
        value() {
            this.lastUpdated = Date.now();
        }
    }
}
</script>

<style scoped>
.progress-component {
    width: 100%;
    margin: 15px 0;
}

.progress-container {
    width: 100%;
    height: 8px;
    background-color: var(--background-color);
    border-radius: 4px;
    overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-bar {
    height: 100%;
    background-color: var(--primary-color);
    background-image: linear-gradient(45deg,
            rgba(255, 255, 255, 0.15) 25%,
            transparent 25%,
            transparent 50%,
            rgba(255, 255, 255, 0.15) 50%,
            rgba(255, 255, 255, 0.15) 75%,
            transparent 75%);
    background-size: 20px 20px;
    border-radius: 4px;
    transition: width 0.3s ease;
    animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
    from {
        background-position: 0 0;
    }

    to {
        background-position: 20px 0;
    }
}

.progress-info {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    margin-top: 8px;
    color: var(--text-color);
    opacity: 0.8;
}

.progress-message {
    font-size: 0.9rem;
    color: var(--text-color);
    opacity: 0.7;
    margin-top: 10px;
    text-align: center;
}

@media (max-width: 768px) {
    .progress-info {
        flex-direction: column;
        align-items: flex-start;
        gap: 5px;
    }
}
</style>