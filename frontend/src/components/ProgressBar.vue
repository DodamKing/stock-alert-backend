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
    computed: {
        remainingTimeText() {
            if (!this.startTime) return "계산 중...";

            const elapsed = (Date.now() - this.startTime) / 1000;
            const remaining = Math.max(0, Math.round(this.estimatedTime - elapsed));

            if (remaining <= 0) return "곧 완료됩니다...";
            if (remaining < 60) return `${remaining}초`;
            return `약 ${Math.ceil(remaining / 60)}분`;
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