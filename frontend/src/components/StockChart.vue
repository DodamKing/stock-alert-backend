<!-- StockChart.vue -->
<template>
    <div class="stock-chart-component">
        <div class="chart-header">
            <h3>가격 차트</h3>
            <div class="chart-type-selector">
                <button v-for="type in availableChartTypes" :key="type.id" @click="selectChartType(type.id)"
                    :class="{ active: selectedChartType === type.id }" class="chart-type-btn">
                    {{ type.label }}
                </button>
            </div>
        </div>

        <div v-if="loading" class="chart-loading">
            <div class="spinner-small"></div>
            <p>차트 데이터 로딩 중...</p>
        </div>

        <div v-else-if="error" class="chart-error">
            <p>{{ error }}</p>
        </div>

        <div v-else-if="!chartData" class="chart-placeholder">
            <p>차트 데이터를 불러오는 중입니다...</p>
        </div>

        <div v-else ref="chartRef" class="chart-wrapper"></div>

        <div v-if="chartData" class="chart-period-info">
            <span v-if="period === 90">3개월 분석 | </span>
            <span v-else-if="period === 365">1년 분석 | </span>
            <span v-else-if="period === 1095">3년 분석 | </span>
            <span v-else-if="period === 1825">5년 분석 | </span>
            <span v-else-if="period === 3650">10년 분석 | </span>
            <span v-else-if="period === 0">전체 기간 분석 | </span>
            <span v-else>{{ period }}일 분석 | </span>
            {{ formatDate(chartData.timeframe?.start) }} ~ {{ formatDate(chartData.timeframe?.end) }}

            <span v-if="chartData.timeframe?.days && chartData.timeframe?.days < period" class="period-mismatch-info">
                (데이터는 {{ chartData.timeframe.days }}일만 존재합니다)
            </span>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import ApexCharts from 'apexcharts';

const props = defineProps({
    chartData: {
        type: Object,
        required: true
    },
    period: {
        type: Number,
        default: 365
    },
    peakDate: {
        type: String,
        default: ''
    },
    peakPrice: {
        type: Number,
        default: 0
    },
});

// 상태 변수들
const loading = ref(false);
const error = ref(null);
const selectedChartType = ref('line');
const chartRef = ref(null);
const chart = ref(null);
const isMobile = ref(false);

// 차트 타입 옵션
const availableChartTypes = computed(() => {
    return [
        { id: 'line', label: '라인' },
        { id: 'area', label: '영역' }
    ];
});

// 모바일 여부 감지 함수
const checkDeviceType = () => {
    isMobile.value = window.innerWidth <= 768;
    if (chart.value) {
        updateChartForMobile();
    }
};

// 모바일 환경에 맞게 차트 옵션 조정
const updateChartForMobile = () => {
    if (!chart.value) return;

    const mobileOptions = isMobile.value ? {
        chart: {
            toolbar: {
                tools: {
                    // 모바일에서는 핵심 도구만 표시
                    download: true,
                    zoom: true,
                    reset: true,
                    // 작은 화면에서는 불필요한 도구 숨김
                    selection: false,
                    zoomin: false,
                    zoomout: false,
                    pan: false
                }
            }
        },
        // 모바일에서 X축 라벨 간소화
        xaxis: {
            labels: {
                datetimeUTC: false,
                format: 'yy-MM',
                rotate: 0,
                style: {
                    fontSize: '10px'
                }
            }
        },
        // 모바일에서 Y축 라벨 간소화
        yaxis: {
            labels: {
                style: {
                    fontSize: '10px'
                }
            }
        }
    } : {};

    chart.value.updateOptions(mobileOptions);
};

// 차트 옵션 계산
const chartOptions = computed(() => {
    if (!props.chartData) return {};

    // 요청 기간 계산 (현재 날짜에서 days만큼 뺀 날짜)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - props.period);

    const baseOptions = {
        chart: {
            type: selectedChartType.value,
            height: isMobile.value ? 280 : 350, // 모바일에서 높이 감소
            toolbar: {
                show: true,
                tools: {
                    download: true,
                    selection: !isMobile.value,
                    zoom: true,
                    zoomin: !isMobile.value,
                    zoomout: !isMobile.value,
                    pan: !isMobile.value,
                    reset: true
                }
            },
            animations: {
                enabled: true,
                speed: isMobile.value ? 300 : 800 // 모바일에서 애니메이션 속도 향상
            },
            background: 'transparent'
        },
        stroke: {
            curve: 'smooth',
            width: 2
        },
        fill: {
            type: selectedChartType.value === 'area' ? 'gradient' : 'solid',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.7,
                opacityTo: 0.3,
                stops: [0, 90, 100]
            }
        },
        dataLabels: {
            enabled: false
        },
        xaxis: {
            type: 'datetime',
            min: startDate.getTime(),
            max: endDate.getTime(),
            labels: {
                datetimeUTC: false,
                format: isMobile.value ? 'yy-MM' : 'yy-MM-dd', // 모바일에서 간결한 포맷
                style: {
                    fontSize: isMobile.value ? '10px' : '12px'
                }
            },
            tooltip: {
                enabled: true
            }
        },
        yaxis: {
            labels: {
                formatter: (value) => {
                    return new Intl.NumberFormat('ko-KR', {
                        maximumFractionDigits: 0
                    }).format(value);
                },
                style: {
                    fontSize: isMobile.value ? '10px' : '12px'
                }
            },
            title: {
                text: isMobile.value ? '' : '가격' // 모바일에서는 타이틀 숨김
            }
        },
        tooltip: {
            x: {
                format: 'yyyy-MM-dd'
            },
            y: {
                formatter: (value) => {
                    return new Intl.NumberFormat('ko-KR', {
                        maximumFractionDigits: 0
                    }).format(value);
                }
            }
        },
        annotations: {
            yaxis: [
                {
                    y: props.peakPrice,
                    borderColor: '#FF4560',
                    label: {
                        borderColor: '#FF4560',
                        style: {
                            color: '#fff',
                            background: '#FF4560',
                            fontSize: isMobile.value ? '10px' : '12px'
                        },
                        text: '전고점'
                    }
                }
            ]
        },
        theme: {
            mode: document.body.classList.contains('dark-mode') ? 'dark' : 'light'
        },
        grid: {
            borderColor: '#90A4AE30',
            xaxis: {
                lines: {
                    show: true
                }
            }
        },
        colors: ['#2E93fA', '#66DA26', '#546E7A', '#FF4560'],
        legend: {
            show: true,
            position: 'top',
            fontSize: isMobile.value ? '10px' : '12px',
            itemMargin: {
                horizontal: 10,
                vertical: 0
            }
        }
    };

    return baseOptions;
});

// 차트 시리즈 데이터 계산
const chartSeries = computed(() => {
    if (!props.chartData || !props.chartData.series) return [];

    // 종가 데이터 시리즈 생성
    const closeSeries = props.chartData.series.find(s => s.name === '종가');
    if (closeSeries) {
        return [{
            name: '가격',
            type: selectedChartType.value,
            data: closeSeries.data.map(item => ({
                x: new Date(item.date).getTime(),
                y: item.value
            }))
        }];
    }

    return [];
});

// 차트 업데이트 또는 생성 함수
const updateChart = () => {
    if (!chartRef.value || !props.chartData) return;

    loading.value = true;

    const options = {
        ...chartOptions.value,
        series: chartSeries.value
    };

    // 차트가 이미 생성되었으면 업데이트, 아니면 새로 생성
    if (chart.value) {
        chart.value.updateOptions(options);
    } else {
        nextTick(() => {
            chart.value = new ApexCharts(chartRef.value, options);
            chart.value.render();
        });
    }
    loading.value = false;
};

// 차트 타입 선택 함수
const selectChartType = (type) => {
    selectedChartType.value = type;
    updateChart();
};

// 날짜 포맷 함수
const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
};

// 차트 리사이즈 핸들러
const handleResize = () => {
    checkDeviceType();
    if (chart.value) {
        chart.value.render();
    }
};

watch(() => props.chartData, (newData) => {
    if (newData) {
        error.value = null;

        nextTick(() => {
            updateChart();
        });
    }
}, { deep: true, immediate: true });

watch(() => props.peakPrice, (newPrice) => {
    if (chart.value && newPrice) {
        // 전고점 주석 업데이트
        chart.value.updateOptions({
            annotations: {
                yaxis: [{
                    y: newPrice,
                    borderColor: '#FF4560',
                    label: {
                        borderColor: '#FF4560',
                        style: {
                            color: '#fff',
                            background: '#FF4560',
                            fontSize: isMobile.value ? '10px' : '12px'
                        },
                        text: '전고점'
                    }
                }]
            }
        });
    }
});

// 라이프사이클 훅
onMounted(() => {
    checkDeviceType();
    window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
    // 차트 인스턴스 정리
    if (chart.value) {
        chart.value.destroy();
    }
    window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.stock-chart-component {
    margin: 1.5rem 0;
    padding: 1rem;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.chart-header h3 {
    margin: 0;
    font-size: 1.2rem;
}

.chart-type-selector {
    display: flex;
    gap: 0.5rem;
}

.chart-type-btn {
    padding: 0.3rem 0.7rem;
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    color: inherit;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s ease;
    min-height: 36px;
    /* 터치 영역 확보 */
}

.chart-type-btn:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

.chart-type-btn.active {
    background-color: rgba(255, 255, 255, 0.3);
    font-weight: 600;
}

.chart-loading,
.chart-placeholder,
.chart-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 350px;
    background-color: rgba(0, 0, 0, 0.05);
    border-radius: 0.5rem;
}

.chart-error {
    color: #f44336;
}

.chart-wrapper {
    margin-top: 1rem;
    height: 350px;
}

.chart-period-info {
    margin-top: 0.5rem;
    text-align: center;
    font-size: 0.85rem;
    opacity: 0.7;
}

.period-mismatch-info {
    color: #FFC107;
    font-weight: 500;
    margin-left: 6px;
}

/* 다크 모드 대응 */
:deep(.dark-mode) .stock-chart-component {
    background-color: rgba(0, 0, 0, 0.2);
}

:deep(.dark-mode) .chart-type-btn {
    background-color: rgba(0, 0, 0, 0.2);
    border-color: rgba(255, 255, 255, 0.1);
}

:deep(.dark-mode) .chart-type-btn:hover {
    background-color: rgba(0, 0, 0, 0.3);
}

:deep(.dark-mode) .chart-type-btn.active {
    background-color: rgba(0, 0, 0, 0.4);
}

:deep(.dark-mode) .chart-loading,
:deep(.dark-mode) .chart-placeholder,
:deep(.dark-mode) .chart-error {
    background-color: rgba(0, 0, 0, 0.1);
}

/* 모바일 최적화 */
@media (max-width: 768px) {
    .stock-chart-component {
        padding: 0.75rem;
        margin: 1rem 0;
    }

    .chart-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }

    .chart-header h3 {
        font-size: 1.1rem;
    }

    .chart-type-selector {
        width: 100%;
    }

    .chart-type-btn {
        flex: 1;
        text-align: center;
        padding: 0.3rem 0.4rem;
        font-size: 0.8rem;
    }

    .chart-loading,
    .chart-placeholder,
    .chart-error {
        height: 250px;
        /* 모바일에서 로딩/오류 영역 높이 감소 */
    }

    .chart-wrapper {
        height: 280px;
        /* 모바일에서 차트 높이 감소 */
    }

    .chart-period-info {
        font-size: 0.75rem;
        margin-top: 0.4rem;
    }

    /* 모바일에서 터치 피드백 개선 */
    .chart-type-btn:active {
        opacity: 0.7;
    }

    /* 너무 작은 텍스트 피하기 */
    .period-mismatch-info {
        display: block;
        margin-top: 0.3rem;
        margin-left: 0;
    }
}

/* 작은 모바일 화면 */
@media (max-width: 480px) {
    .stock-chart-component {
        padding: 0.5rem;
    }

    .chart-header h3 {
        font-size: 1rem;
    }

    .chart-wrapper {
        height: 250px;
        /* 더 작은 화면에서 차트 높이 추가 감소 */
    }
}
</style>