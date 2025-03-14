<!-- PeriodSelector.vue -->
<template>
    <div class="period-selector-component">
        <div class="period-label">분석 기간:</div>
        <div class="period-options">
            <button v-for="(option, key) in periodOptions" :key="key" @click="selectPeriod(option.days)"
                :class="{ active: selectedPeriod === option.days }" class="period-btn">
                {{ option.label }}
            </button>
        </div>
    </div>
</template>

<script>
export default {
    name: 'PeriodSelector',
    props: {
        value: {
            type: Number,
            default: 365
        }
    },
    data() {
        return {
            selectedPeriod: this.value,
            periodOptions: {
                short: { label: '3개월', days: 90 },
                medium: { label: '1년', days: 365 },
                long1: { label: '3년', days: 1095 },
                long2: { label: '5년', days: 1825 },
                long3: { label: '10년', days: 3650 },
                // full: { label: '전체', days: 0 }
            }
        };
    },
    methods: {
        selectPeriod(days) {
            this.selectedPeriod = days;
            this.$emit('input', days);
            this.$emit('period-changed', days);
        }
    }
};
</script>

<style scoped>
/* 새로운 클래스명을 사용하여 충돌 방지 */
.period-selector-component {
    margin: 1rem 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.period-selector-component .period-label {
    font-weight: 500;
    margin-bottom: 0.25rem;
}

.period-selector-component .period-options {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.period-selector-component .period-btn {
    padding: 0.5rem 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background-color: rgba(255, 255, 255, 0.1);
    color: inherit;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem;
    min-height: 36px;
}

.period-selector-component .period-btn:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

.period-selector-component .period-btn.active {
    background-color: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.5);
    font-weight: 600;
}

/* 다크 모드 대응 */
:deep(.dark-mode) .period-selector-component .period-btn {
    border-color: rgba(0, 0, 0, 0.2);
    background-color: rgba(0, 0, 0, 0.1);
}

:deep(.dark-mode) .period-selector-component .period-btn:hover {
    background-color: rgba(0, 0, 0, 0.2);
}

:deep(.dark-mode) .period-selector-component .period-btn.active {
    background-color: rgba(0, 0, 0, 0.3);
    border-color: rgba(0, 0, 0, 0.5);
}

/* 모바일 최적화 */
@media (max-width: 768px) {
    .period-selector-component .period-options {
        justify-content: space-between;
        width: 100%;
    }

    .period-selector-component .period-btn {
        padding: 0.5rem 0.6rem;
    }
}

/* 작은 모바일 화면 */
@media (max-width: 480px) {
    .period-selector-component .period-btn {
        padding: 0.5rem 0.4rem;
        font-size: 0.85rem;
    }
}
</style>