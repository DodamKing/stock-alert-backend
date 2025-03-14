<!-- components/DCABacktest.vue -->
<template>
    <div class="dca-backtest">
        <h2>적립식 투자 시뮬레이션</h2>
        <p class="description">정기적으로 투자했을 때의 수익률을 계산해보세요</p>

        <!-- 설정 영역 -->
        <div class="settings-container" v-if="!isLoading && !result">
            <div class="settings-section">
                <h3>종목 선택</h3>
                <div class="stock-selector">
                    <div class="stock-input">
                        <input type="text" v-model="searchQuery" @keyup.enter="searchStocks" placeholder="종목명 또는 심볼 검색"
                            :disabled="selectedStocks.length >= 5" />
                        <button @click="searchStocks" :disabled="selectedStocks.length >= 5">
                            검색
                        </button>
                    </div>
                    <div class="search-results" v-if="searchResults.length > 0">
                        <div v-for="stock in searchResults" :key="stock.symbol" class="search-result-item"
                            @click="addStock(stock)">
                            <div class="stock-name">{{ stock.name }}</div>
                            <div class="stock-symbol">{{ stock.symbol }}</div>
                            <div class="stock-market" :class="stock.type">{{ getMarketDisplayName(stock.market) }}</div>
                        </div>
                    </div>

                    <div class="selected-stocks">
                        <div v-for="stock in selectedStocks" :key="stock.symbol" class="selected-stock"
                            :class="stock.type">
                            <div class="stock-info">
                                <div class="stock-name">{{ stock.name }}</div>
                                <div class="stock-symbol">{{ stock.symbol }}</div>
                            </div>
                            <div class="stock-allocation">
                                <input type="number" v-model.number="stock.allocation" min="1" max="100"
                                    @input="updateAllocations(stock)" />
                                <span>%</span>
                            </div>
                            <button class="remove-stock" @click="removeStock(stock)">✕</button>
                        </div>

                        <div class="allocation-total" :class="{ 'error': totalAllocation !== 100 }">
                            총 비중: {{ totalAllocation }}% {{ totalAllocation !== 100 ? '(100%가 되도록 설정해주세요)' : '' }}
                        </div>
                    </div>
                </div>
            </div>

            <div class="settings-section">
                <h3>투자 기간 및 금액 설정</h3>
                <div class="date-inputs">
                    <div class="input-group">
                        <label>시작일</label>
                        <input type="date" v-model="startDate" :max="today" />
                    </div>
                    <div class="input-group">
                        <label>종료일</label>
                        <input type="date" v-model="endDate" :min="startDate" :max="today" />
                    </div>
                </div>

                <div class="amount-inputs">
                    <div class="input-group">
                        <label>초기 투자금액</label>
                        <div class="amount-input">
                            <input type="number" v-model.number="initialAmount" min="0" step="100000" />
                            <span>원</span>
                        </div>
                    </div>
                    <div class="input-group">
                        <label>정기 투자금액</label>
                        <div class="amount-input">
                            <input type="number" v-model.number="investmentAmount" min="0" step="10000" />
                            <span>원</span>
                        </div>
                    </div>
                </div>

                <div class="frequency-selector">
                    <label>투자 주기</label>
                    <div class="frequency-options">
                        <button v-for="(label, value) in frequencyOptions" :key="value"
                            :class="{ active: investmentFrequency === value }" @click="investmentFrequency = value">
                            {{ label }}
                        </button>
                    </div>
                </div>

                <div class="fee-settings">
                    <div class="input-group">
                        <label>매매 수수료 (%)</label>
                        <input type="number" v-model.number="feeRate" min="0" max="10" step="0.001" />
                    </div>
                    <div class="input-group">
                        <label>세금 (%)</label>
                        <input type="number" v-model.number="taxRate" min="0" max="50" step="0.1" />
                    </div>
                </div>
            </div>

            <div class="actions">
                <button class="run-backtest" @click="runBacktest" :disabled="!isValid || isLoading">
                    {{ isLoading ? '계산 중...' : '백테스트 실행' }}
                </button>
            </div>
        </div>

        <!-- 로딩 표시 -->
        <div class="loading" v-if="isLoading">
            <h3>백테스팅 진행 중...</h3>

            <ProgressBar :value="progress" :start-time="startTime" :estimated-time="estimatedTime"
                :message="`${selectedStocks.length}개 종목, ${periodYears}년 기간의 데이터를 분석 중입니다.`" />
        </div>

        <!-- 에러 메시지 -->
        <div class="error-message" v-if="error">
            <p>{{ error }}</p>
            <button @click="error = null">다시 시작하기</button>
        </div>

        <!-- 결과 표시 -->
        <div class="results-container" v-if="result && !isLoading">
            <button class="back-button" @click="resetBacktest">
                <span>←</span> 설정으로 돌아가기
            </button>

            <div class="summary-card">
                <h3>투자 성과 요약</h3>
                <div class="performance-score">
                    <div class="score-circle" :class="getScoreClass(result.summary.performance_score)">
                        {{ result.summary.performance_score }}
                    </div>
                    <div class="score-label">성과 점수</div>
                </div>

                <div class="summary-metrics">
                    <div class="metric">
                        <div class="metric-value">{{ formatNumber(result.summary.total_invested) }}원</div>
                        <div class="metric-label">총 투자금액</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ formatNumber(result.summary.final_value) }}원</div>
                        <div class="metric-label">최종 가치</div>
                    </div>
                    <div class="metric" :class="result.summary.total_profit >= 0 ? 'positive' : 'negative'">
                        <div class="metric-value">{{ formatNumber(result.summary.total_profit) }}원</div>
                        <div class="metric-label">총 수익</div>
                    </div>
                    <div class="metric" :class="result.summary.total_profit_pct >= 0 ? 'positive' : 'negative'">
                        <div class="metric-value">{{ result.summary.total_profit_pct.toFixed(2) }}%</div>
                        <div class="metric-label">총 수익률</div>
                    </div>
                    <div class="metric" :class="result.summary.cagr >= 0 ? 'positive' : 'negative'">
                        <div class="metric-value">{{ result.summary.cagr.toFixed(2) }}%</div>
                        <div class="metric-label">연평균 수익률(CAGR)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ result.summary.cagr_rating }}</div>
                        <div class="metric-label">CAGR 등급</div>
                    </div>
                </div>

                <div class="analysis-comment" v-if="result.analysis && result.analysis.comment">
                    {{ result.analysis.comment }}
                </div>
            </div>

            <div class="chart-container">
                <h3>포트폴리오 가치 변화</h3>
                <div ref="chartContainer" class="chart"></div>
            </div>

            <div class="portfolio-composition">
                <h3>최종 포트폴리오 구성</h3>
                <div class="portfolio-table">
                    <table>
                        <thead>
                            <tr>
                                <th>종목명</th>
                                <th>보유 수량</th>
                                <th>투자 금액</th>
                                <th>현재 가치</th>
                                <th>비중</th>
                                <th>수익률</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="item in result.portfolio" :key="item.symbol">
                                <td>
                                    <div class="stock-name">{{ item.name || item.symbol }}</div>
                                    <div class="stock-symbol">{{ item.symbol }}</div>
                                </td>
                                <td>{{ item.shares.toFixed(4) }}</td>
                                <td>{{ formatNumber(item.cost_basis) }}원</td>
                                <td>{{ formatNumber(item.current_value) }}원</td>
                                <td>{{ item.weight.toFixed(2) }}%</td>
                                <td :class="item.profit_loss_pct >= 0 ? 'positive' : 'negative'">
                                    {{ item.profit_loss_pct.toFixed(2) }}%
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="transactions-container">
                <h3>주요 거래 내역</h3>
                <div class="transactions-header">
                    <span>총 {{ result.summary.transactions_count }}건의 거래가 있었습니다.</span>
                    <button v-if="!showAllTransactions" @click="showAllTransactions = true">모든 거래 보기</button>
                    <button v-else @click="showAllTransactions = false">주요 거래만 보기</button>
                </div>

                <div class="transactions-table">
                    <table>
                        <thead>
                            <tr>
                                <th>날짜</th>
                                <th>유형</th>
                                <th>금액</th>
                                <th>상세 내역</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(transaction, index) in displayedTransactions" :key="index">
                                <td>{{ formatDate(transaction.date) }}</td>
                                <td>{{ transaction.type === 'initial' ? '초기 투자' : '정기 투자' }}</td>
                                <td>{{ formatNumber(transaction.amount) }}원</td>
                                <td>
                                    <div v-for="(detail, symbol) in transaction.details" :key="symbol"
                                        class="transaction-detail">
                                        {{ getStockName(symbol) }}: {{ detail.shares.toFixed(4) }}주 ({{
                                        formatNumber(detail.amount) }}원)
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import ApexCharts from 'apexcharts';
import ProgressBar from './ProgressBar.vue';

export default {
    name: 'DCABacktest',
    components: {
        ProgressBar
    },
    data() {
        const today = new Date().toISOString().split('T')[0];
        // 기본 시작일: 3년 전
        const defaultStartDate = new Date();
        defaultStartDate.setFullYear(defaultStartDate.getFullYear() - 3);

        return {
            apiBaseUrl: import.meta.env.VITE_API_URL || '/api',
            
            // 검색 관련
            searchQuery: '',
            searchResults: [],

            // 선택된 종목
            selectedStocks: [],

            // 투자 설정
            startDate: defaultStartDate.toISOString().split('T')[0],
            endDate: today,
            today: today,
            initialAmount: 5000000, // 500만원
            investmentAmount: 500000, // 50만원
            investmentFrequency: 'monthly',
            frequencyOptions: {
                monthly: '매월',
                quarterly: '분기별',
                yearly: '매년'
            },
            feeRate: 0.015, // 0.015%
            taxRate: 0.3, // 0.3%

            // 상태 관리
            isLoading: false,
            error: null,
            result: null,
            chart: null,
            showAllTransactions: false,

            // 프로그래스바
            progress: 0,
            startTime: null,
            estimatedTime: 0,
            progressInterval: null
        };
    },
    computed: {
        totalAllocation() {
            return this.selectedStocks.reduce((sum, stock) => sum + (stock.allocation || 0), 0);
        },
        isValid() {
            return this.selectedStocks.length > 0 &&
                this.totalAllocation === 100 &&
                this.startDate &&
                this.endDate &&
                new Date(this.startDate) < new Date(this.endDate);
        },
        displayedTransactions() {
            if (!this.result || !this.result.transactions) return [];

            if (this.showAllTransactions) {
                return this.result.transactions;
            } else {
                // 첫 번째 거래와 최대 5개의 다른 거래 표시
                return this.result.transactions.slice(0, 6);
            }
        },
        periodYears() {
            if (!this.startDate || !this.endDate) return 0;
            const start = new Date(this.startDate);
            const end = new Date(this.endDate);
            return ((end - start) / (1000 * 60 * 60 * 24 * 365.25)).toFixed(1);
        }
    },
    methods: {
        async searchStocks() {
            if (!this.searchQuery.trim()) return;

            try {
                this.isLoading = true;

                // 일단 한국 시장만 먼저 하고 나중에 다시 하자자
                // fetch API 사용
                const response = await fetch(`${this.apiBaseUrl}/search?query=${encodeURIComponent(this.searchQuery)}&markets=ks,kq,etf&limit=10`);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.status === 'success') {
                    // 이미 선택된 종목 필터링
                    const selectedSymbols = this.selectedStocks.map(s => s.symbol);
                    this.searchResults = data.data.filter(s => !selectedSymbols.includes(s.symbol));
                } else {
                    this.error = '종목 검색 중 오류가 발생했습니다.';
                }
            } catch (error) {
                console.error('종목 검색 오류:', error);
                this.error = '종목 검색 중 오류가 발생했습니다.';
            } finally {
                this.isLoading = false;
            }
        },

        addStock(stock) {
            if (this.selectedStocks.length >= 5) return;

            // 각 종목에 기본 비중 할당 (균등 분배)
            const newStock = {
                ...stock,
                allocation: Math.floor(100 / (this.selectedStocks.length + 1))
            };

            this.selectedStocks.push(newStock);

            // 나머지 종목들의 비중 재조정
            this.redistributeAllocations();

            // 검색 결과 비우기
            this.searchResults = [];
            this.searchQuery = '';
        },

        removeStock(stockToRemove) {
            this.selectedStocks = this.selectedStocks.filter(s => s.symbol !== stockToRemove.symbol);

            // 남은 종목들의 비중 재조정
            this.redistributeAllocations();
        },

        updateAllocations(changedStock) {
            // 입력값 유효성 확인 및 조정
            if (changedStock.allocation < 0) changedStock.allocation = 0;
            if (changedStock.allocation > 100) changedStock.allocation = 100;

            // 모든 종목의 비중이 100%를 넘지 않게 조정
            if (this.totalAllocation > 100) {
                const excess = this.totalAllocation - 100;
                changedStock.allocation -= excess;
            }
        },

        redistributeAllocations() {
            if (this.selectedStocks.length === 0) return;

            // 각 종목에 균등하게 비중 분배
            const equalAllocation = Math.floor(100 / this.selectedStocks.length);
            let remainingAllocation = 100 - (equalAllocation * this.selectedStocks.length);

            this.selectedStocks.forEach((stock, index) => {
                stock.allocation = equalAllocation;

                // 나머지 1% 분배
                if (index < remainingAllocation) {
                    stock.allocation += 1;
                }
            });
        },

        async runBacktest() {
            if (!this.isValid) return;

            try {
                this.isLoading = true;
                this.error = null;

                // 예상 시간 계산 및 프로그레스 시작
                this.estimatedTime = this.calculateEstimatedTime();
                this.startTime = Date.now();
                this.startProgressAnimation();

                // 백테스팅 파라미터 생성 (기존 코드)
                const params = {
                    symbols: this.selectedStocks.map(s => s.symbol),
                    allocation: this.selectedStocks.reduce((acc, stock) => {
                        acc[stock.symbol] = stock.allocation;
                        return acc;
                    }, {}),
                    start_date: this.startDate,
                    end_date: this.endDate,
                    initial_amount: this.initialAmount,
                    investment_amount: this.investmentAmount,
                    investment_frequency: this.investmentFrequency,
                    fee_rate: this.feeRate,
                    tax_rate: this.taxRate
                };

                // 백테스팅 API 호출 (기존 코드)
                const response = await fetch(`${this.apiBaseUrl}/backtest/dca`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(params)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.status === 'success') {
                    this.result = data.data;

                    // 프로그레스 완료 처리
                    this.completeProgress();

                    // 차트 렌더링 (기존 코드)
                    this.$nextTick(() => {
                        this.renderChart();
                    });
                } else {
                    this.error = '백테스팅 중 오류가 발생했습니다.';
                }
            } catch (error) {
                console.error('백테스팅 오류:', error);
                this.error = error.message || '백테스팅 중 오류가 발생했습니다.';
                this.completeProgress();
            } finally {
                this.isLoading = false;
            }
        },

        resetBacktest() {
            this.result = null;
            if (this.chart) {
                this.chart.destroy();
                this.chart = null;
            }
        },

        renderChart() {
            if (!this.result || !this.result.value_history || !this.$refs.chartContainer) return;

            // 차트 데이터 준비
            const chartData = this.result.value_history.map(item => ({
                x: new Date(item.date).getTime(),
                y: Math.round(item.value)
            }));

            const investedData = this.result.value_history.map(item => ({
                x: new Date(item.date).getTime(),
                y: Math.round(item.invested)
            }));

            const options = {
                chart: {
                    type: 'line',
                    height: 350,
                    zoom: {
                        enabled: true
                    },
                    toolbar: {
                        show: true
                    },
                    background: 'transparent'
                },
                stroke: {
                    curve: 'smooth',
                    width: [4, 2]
                },
                colors: ['#4CAF50', '#2196F3'],
                series: [
                    {
                        name: '포트폴리오 가치',
                        data: chartData
                    },
                    {
                        name: '총 투자금액',
                        data: investedData
                    }
                ],
                xaxis: {
                    type: 'datetime',
                    labels: {
                        datetimeUTC: false,
                        format: 'yy-MM-dd'
                    }
                },
                yaxis: {
                    labels: {
                        formatter: (value) => {
                            return this.formatNumber(value) + '원';
                        }
                    },
                    title: {
                        text: '금액 (원)'
                    }
                },
                tooltip: {
                    x: {
                        format: 'yyyy-MM-dd'
                    },
                    y: {
                        formatter: (value) => {
                            return this.formatNumber(value) + '원';
                        }
                    }
                },
                legend: {
                    position: 'top'
                },
                grid: {
                    borderColor: '#90A4AE30'
                },
                theme: {
                    mode: document.body.classList.contains('dark-mode') ? 'dark' : 'light'
                }
            };

            // 기존 차트가 있으면 제거
            if (this.chart) {
                this.chart.destroy();
            }

            // 새 차트 생성
            this.chart = new ApexCharts(this.$refs.chartContainer, options);
            this.chart.render();
        },

        formatNumber(value) {
            return new Intl.NumberFormat('ko-KR').format(Math.round(value));
        },

        formatDate(dateStr) {
            const date = new Date(dateStr);
            return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
        },

        getMarketDisplayName(market) {
            const marketMap = {
                'KOSPI': '코스피',
                'KOSDAQ': '코스닥',
                'NASDAQ': '나스닥',
                'NYSE': '뉴욕',
                'AMEX': '아멕스',
                'ETF/KR': 'ETF(KR)',
                'ETF/US': 'ETF(US)'
            };
            return marketMap[market] || market;
        },

        getScoreClass(score) {
            if (score >= 80) return 'excellent';
            if (score >= 60) return 'good';
            if (score >= 40) return 'average';
            if (score >= 20) return 'below-average';
            return 'poor';
        },

        getStockName(symbol) {
            const stock = this.selectedStocks.find(s => s.symbol === symbol);
            return stock ? stock.name : symbol;
        },

        calculateEstimatedTime() {
            // 데이터 양과 종목 수에 따라 예상 시간 계산 (단위: 초)
            const stockCount = this.selectedStocks.length;
            const days = (new Date(this.endDate) - new Date(this.startDate)) / (1000 * 60 * 60 * 24);

            // 기본 5초 + 종목 당 2초 + 날짜 범위에 따른 추가 시간
            return Math.min(5 + (stockCount * 2) + (days / 50), 120);
        },

        startProgressAnimation() {
            // 초기 프로그레스 10%로 설정 (데이터 요청 시작)
            this.progress = 10;

            // 이전 인터벌이 있다면 정리
            if (this.progressInterval) {
                clearInterval(this.progressInterval);
            }

            // 부드러운 프로그레스 애니메이션
            this.progressInterval = setInterval(() => {
                const elapsed = (Date.now() - this.startTime) / 1000;
                const ratio = elapsed / this.estimatedTime;

                // 0-95%까지만 자동 증가 (실제 완료는 응답 후 100%로 설정)
                if (ratio < 0.95) {
                    // 처음에는 빠르게, 나중에는 천천히 증가하는 비선형 곡선
                    this.progress = 10 + (ratio * 85);
                } else {
                    this.progress = 95; // 최대 95%까지만
                }
            }, 200);
        },

        completeProgress() {
            if (this.progressInterval) {
                clearInterval(this.progressInterval);
                this.progressInterval = null;
            }
            this.progress = 100;
        },
    },
    beforeDestroy() {
        if (this.chart) {
            this.chart.destroy();
        }

        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
    }
};
</script>

<style>
@import '../assets/css/dcabacktest.css';
</style>