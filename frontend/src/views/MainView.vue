<!-- MainView.vue -->
<template>
    <div class="app-container" :class="{ 'dark-mode': isDarkMode }">
        <header>
            <h1>
                <transition name="fade" appear>
                    <span>주식 전고점 대비 하락률 조회</span>
                </transition>
            </h1>
            <transition name="slide-down" appear>
                <p class="subtitle">전고점 대비 하락 정도를 확인하고 매수 시점을 판단해보세요</p>
            </transition>
            <div class="theme-toggle" @click="toggleDarkMode">
                <span v-if="isDarkMode">🌞</span>
                <span v-else>🌙</span>
            </div>
        </header>

        <transition name="fade" appear>
            <div class="search-container">
                <div class="search-box">
                    <input type="text" v-model="searchQuery" @keyup.enter="searchStocks"
                        placeholder="주식 이름을 입력하세요 (예: 삼성전자, NAVER, Apple...)" ref="searchInput" />
                    <button @click="searchStocks" :disabled="loading" class="pulse-on-hover">
                        <span v-if="!loading">검색</span>
                        <span v-else class="spinner-small"></span>
                    </button>
                </div>

                <!-- 필터 섹션 수정 -->
                <div class="filter-section">
                    <!-- 모바일에서만 표시되는 토글 버튼 -->
                    <div v-if="isMobile" class="filter-toggle" @click="toggleFilterVisibility">
                        <span>시장 필터</span>
                        <span>{{ isFilterVisible ? '▲' : '▼' }}</span>
                    </div>

                    <!-- v-show로 모바일에서만 토글, 데스크톱에서는 항상 표시 -->
                    <div class="market-filter" v-show="!isMobile || isFilterVisible">
                        <span>시장 필터:</span>
                        <div class="filter-options">
                            <label><input type="checkbox" v-model="markets.kospi"> 코스피</label>
                            <label><input type="checkbox" v-model="markets.kosdaq"> 코스닥</label>
                            <label><input type="checkbox" v-model="markets.us"> 미국</label>
                            <label><input type="checkbox" v-model="markets.etf"> ETF</label>
                        </div>
                        <button @click="saveUserPreferences" class="save-btn">저장</button>
                    </div>
                </div>
            </div>
        </transition>

        <!-- 로딩 표시 -->
        <transition name="fade" mode="out-in">
            <div v-if="loading" class="loading">
                <div class="spinner"></div>
                <p>데이터를 가져오는 중입니다...</p>
            </div>
        </transition>

        <!-- 검색 결과 목록 -->
        <transition name="slide-up" mode="out-in">
            <div v-if="searchResults.length > 0 && !stockData" class="search-results">
                <h2>검색 결과</h2>
                <p>{{ searchResults.length }}개의 결과가 검색되었습니다.</p>

                <transition-group name="list" tag="div" class="results-grid">
                    <div v-for="(stock, index) in searchResults" :key="stock.symbol" class="stock-item"
                        @click="getStockData(stock.symbol, stock.market)"
                        :style="{ animationDelay: index * 0.05 + 's' }">
                        <div class="stock-name">{{ stock.name }}</div>
                        <div class="stock-symbol">{{ stock.symbol }}</div>
                        <div class="stock-market" :class="stock.type">{{ getMarketDisplayName(stock.market) }}</div>
                    </div>
                </transition-group>
            </div>
        </transition>

        <!-- 전고점 대비 하락률 정보 -->
        <transition name="slide-right" mode="out-in">
            <div v-if="stockData" class="stock-detail">
                <div class="back-button ripple" @click="clearStockData">
                    <span>←</span> 검색 결과로 돌아가기
                </div>

                <div class="stock-header">
                    <h2>{{ stockData.name }}</h2>
                    <div class="stock-meta">
                        <span class="stock-symbol">{{ stockData.symbol }}</span>
                        <span class="stock-market" :class="stockData.type">{{ getMarketDisplayName(stockData.market)
                            }}</span>
                    </div>
                </div>

                <div class="price-container">
                    <div class="current-price">
                        <div class="label">현재가</div>
                        <div class="value">{{ formatPrice(stockData.currentPrice) }}</div>
                    </div>
                    <div class="peak-price">
                        <div class="label">전고점 ({{ formatDate(stockData.peakDate) }})</div>
                        <div class="value">{{ formatPrice(stockData.peakPrice) }}</div>
                    </div>
                </div>

                <!-- 기간 선택기 -->
                <PeriodSelector v-model="selectedPeriod" @period-changed="handlePeriodChange" />

                <!-- 차트 -->
                <StockChart v-if="stockData && stockData.chartData" :chartData="stockData.chartData"
                    :period="selectedPeriod" :peakDate="stockData.peakDate" :peakPrice="stockData.peakPrice" />

                <!-- 전고점 대비 하락률 컴포넌트 사용 -->
                <StockDropInfo :stockData="stockData" :hasNotification="hasNotification"
                    @save-notification="handleSaveNotification" @remove-notification="handleRemoveNotification" />

                <div v-if="stockData.searchResults && stockData.searchResults.otherMatches.length > 0"
                    class="other-matches">
                    <h3>다른 검색 결과</h3>
                    <transition-group name="list" tag="div" class="results-grid">
                        <div v-for="(stock, index) in stockData.searchResults.otherMatches" :key="stock.symbol"
                            class="stock-item" @click="getStockData(stock.symbol, stock.market)"
                            :style="{ animationDelay: index * 0.05 + 's' }">
                            <div class="stock-name">{{ stock.name }}</div>
                            <div class="stock-symbol">{{ stock.symbol }}</div>
                            <div class="stock-market" :class="stock.type">{{ getMarketDisplayName(stock.market) }}</div>
                        </div>
                    </transition-group>
                </div>

                <div class="last-update">
                    마지막 업데이트: {{ formatDateTime(stockData.lastUpdate) }}
                </div>
            </div>
        </transition>

        <!-- 오류 메시지 -->
        <transition name="fade" mode="out-in">
            <div v-if="error" class="error-message">
                <p>{{ error }}</p>
            </div>
        </transition>

        <!-- 알림 메시지 -->
        <transition name="toast">
            <div v-if="notification.show" class="notification-toast" :class="notification.type">
                {{ notification.message }}
            </div>
        </transition>

        <footer>
            <div class="footer-content">
                <span class="data-source">📊 FinanceDataReader </span>
                <span class="copyright">© 2025</span>
            </div>
        </footer>
    </div>
</template>

<script>
import StockDropInfo from '../components/StockDropInfo.vue';
import PeriodSelector from '../components/PeriodSelector.vue'
import StockChart from '../components/StockChart.vue';

export default {
    name: 'App',
    components: {
        StockDropInfo,
        PeriodSelector,
        StockChart
    },
    data() {
        return {
            searchQuery: '',
            searchResults: [],
            stockData: null,
            loading: false,
            chartLoading: false,
            error: null,
            markets: {
                kospi: true,
                kosdaq: true,
                us: true,
                etf: true
            },
            apiBaseUrl: import.meta.env.VITE_API_URL || '/api',
            isDarkMode: false,
            notification: {
                show: false,
                message: '',
                type: 'info'
            },
            hasNotification: false,
            notifiedStocks: [],
            selectedPeriod: 365, // 기본값은 1년(365일)
            currentSymbol: null,
            currentMarket: null,
            isFilterVisible: false,
            isMobile: false, 
        };
    },
    mounted() {
        // 사용자 설정 불러오기
        this.loadUserPreferences();

        // 검색 입력란에 포커스
        this.$nextTick(() => {
            if (this.$refs.searchInput) {
                this.$refs.searchInput.focus();
            }
        });

        // 모바일 감지
        this.checkDeviceType();
        window.addEventListener('resize', this.checkDeviceType);

        // 저장된 알림 목록 가져오기
        const savedNotifications = localStorage.getItem('notifiedStocks');
        if (savedNotifications) {
            this.notifiedStocks = JSON.parse(savedNotifications);
        }
    },
    methods: {
        async searchStocks() {
            if (!this.searchQuery.trim()) {
                this.showNotification('검색어를 입력해주세요.', 'warning');
                return;
            }

            this.selectedPeriod = 365;
            this.loading = true;
            this.error = null;
            this.stockData = null;
            this.searchResults = [];

            try {
                // 선택된 시장들 문자열로 변환
                const selectedMarkets = [];
                if (this.markets.kospi) selectedMarkets.push('KOSPI');
                if (this.markets.kosdaq) selectedMarkets.push('KOSDAQ');
                if (this.markets.us) {
                    selectedMarkets.push('NASDAQ');
                    selectedMarkets.push('NYSE');
                    selectedMarkets.push('AMEX');
                }
                if (this.markets.etf) {
                    selectedMarkets.push('ETF/KR');
                    selectedMarkets.push('ETF/US');
                }

                const marketsParam = selectedMarkets.length > 0 ? selectedMarkets.join(',') : '';

                const response = await fetch(
                    `${this.apiBaseUrl}/search?query=${encodeURIComponent(this.searchQuery)}&markets=${encodeURIComponent(marketsParam)}`
                );

                if (!response.ok) {
                    throw new Error('검색 중 오류가 발생했습니다.');
                }

                const data = await response.json();

                if (data.status === 'success') {
                    this.searchResults = data.data;

                    // 검색 결과가 하나도 없으면 에러 메시지 표시
                    if (this.searchResults.length === 0) {
                        this.error = `"${this.searchQuery}"에 대한 검색 결과가 없습니다.`;
                    }
                } else {
                    throw new Error(data.message || '검색 중 오류가 발생했습니다.');
                }
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        async getStockData(symbol, market, isChart) {
            // 새 종목 선택 시 기간 초기화 (이전 종목과 다른 경우만)
            if (this.currentSymbol !== symbol || this.currentMarket !== market) {
                this.selectedPeriod = 365; // 기본값으로 리셋
            }
            
            if (!isChart) this.loading = true;
            this.error = null;

            // 현재 선택된 종목 정보 저장
            this.currentSymbol = symbol;
            this.currentMarket = market;

            try {
                // 1. 전고점 데이터 호출
                const peakResponse = await fetch(
                    `${this.apiBaseUrl}/peak-drop?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}&days=${this.selectedPeriod}`
                );

                if (!peakResponse.ok) {
                    throw new Error('데이터를 가져오는 중 오류가 발생했습니다.');
                }

                const peakData = await peakResponse.json();

                if (peakData.status !== 'success') {
                    throw new Error(peakData.message || '데이터를 가져오는 중 오류가 발생했습니다.');
                }

                // 2. 차트 데이터 호출
                const chartResponse = await fetch(
                    `${this.apiBaseUrl}/chart-data?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}&days=${this.selectedPeriod}`
                );

                if (!chartResponse.ok) {
                    throw new Error('차트 데이터를 가져오는 중 오류가 발생했습니다.');
                }

                const chartData = await chartResponse.json();

                if (chartData.status !== 'success') {
                    throw new Error(chartData.message || '차트 데이터를 가져오는 중 오류가 발생했습니다.');
                }

                // 3. 데이터 설정
                this.stockData = peakData.data;
                this.stockData.chartData = chartData.data; // 차트 데이터를 stockData에 추가

                // 4. 전고점과 차트 데이터 일관성 확인 및 수정
                if (this.stockData.chartData && this.stockData.chartData.peakInfo) {
                    // 전고점 정보를 차트 데이터의 peakInfo로 덮어쓰기
                    this.stockData.chartData.peakInfo = {
                        date: this.stockData.peakDate,
                        price: this.stockData.peakPrice
                    };
                }

                // 저장된 알림 설정이 있는지 확인
                this.hasNotification = this.notifiedStocks.some(item =>
                    item.symbol === this.stockData.symbol
                );

            } catch (err) {
                console.error('데이터 로딩 오류:', err);
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        // 기간이 변경되었을 때 데이터 다시 불러오기
        async handlePeriodChange(days) {
            this.selectedPeriod = days;
            if (this.currentSymbol && this.currentMarket) {
                // 변경된 기간으로 데이터 다시 가져오기
                const isChart = true
                await this.getStockData(this.currentSymbol, this.currentMarket, isChart);
            }
        },

        clearStockData() {
            this.stockData = null;
        },

        formatPrice(price) {
            return new Intl.NumberFormat('ko-KR', {
                maximumFractionDigits: 0
            }).format(price);
        },

        formatDate(dateStr) {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
        },

        formatDateTime(dateTimeStr) {
            if (!dateTimeStr) return '';
            const date = new Date(dateTimeStr);
            return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
        },

        getMarketDisplayName(market) {
            const marketMap = {
                'KOSPI': '코스피',
                'KOSDAQ': '코스닥',
                'NASDAQ': '나스닥',
                'NYSE': '뉴욕',
                'AMEX': '아멕스',
                'ETF/KR': 'ETF'
            };
            return marketMap[market] || market;
        },

        toggleDarkMode() {
            this.isDarkMode = !this.isDarkMode;
            localStorage.setItem('darkMode', this.isDarkMode);
        },

        saveUserPreferences() {
            const preferences = {
                markets: this.markets,
                darkMode: this.isDarkMode
            };

            localStorage.setItem('userPreferences', JSON.stringify(preferences));
            this.showNotification('설정이 저장되었습니다.', 'success');
        },

        loadUserPreferences() {
            const savedPreferences = localStorage.getItem('userPreferences');
            if (savedPreferences) {
                const preferences = JSON.parse(savedPreferences);
                if (preferences.markets) {
                    this.markets = preferences.markets;
                }

                if (preferences.darkMode !== undefined) {
                    this.isDarkMode = preferences.darkMode;
                }
            }

            // 다크모드 설정 확인 (별도 저장되었을 수 있음)
            const darkMode = localStorage.getItem('darkMode');
            if (darkMode !== null) {
                this.isDarkMode = darkMode === 'true';
            }
        },

        showNotification(message, type = 'info', duration = 3000) {
            this.notification = {
                show: true,
                message,
                type
            };

            setTimeout(() => {
                this.notification.show = false;
            }, duration);
        },

        handleSaveNotification(data) {
            // 현재 종목 정보와 임계값을 저장
            const notification = {
                symbol: this.stockData.symbol,
                name: this.stockData.name,
                market: this.stockData.market,
                threshold: data.threshold,
                currentDrop: this.stockData.drop.percent,
                timestamp: new Date().toISOString()
            };

            // 이미 존재하는 알림이 있으면 업데이트
            const existingIndex = this.notifiedStocks.findIndex(item =>
                item.symbol === this.stockData.symbol
            );

            if (existingIndex !== -1) {
                this.notifiedStocks[existingIndex] = notification;
            } else {
                this.notifiedStocks.push(notification);
            }

            // 로컬 스토리지에 저장
            localStorage.setItem('notifiedStocks', JSON.stringify(this.notifiedStocks));

            this.hasNotification = true;
            this.showNotification('알림이 설정되었습니다.', 'success');

            // 알림 권한 요청
            if (Notification && Notification.permission !== 'granted') {
                Notification.requestPermission();
            }
        },

        handleRemoveNotification(symbol) {
            // 알림 제거
            this.notifiedStocks = this.notifiedStocks.filter(item =>
                item.symbol !== symbol
            );
            this.hasNotification = false;
            localStorage.setItem('notifiedStocks', JSON.stringify(this.notifiedStocks));
            this.showNotification('알림이 해제되었습니다.', 'info');
        },

        checkNotifications() {
            // 백그라운드에서 알림 조건 체크 (실제 구현시 서버에서 푸시 알림으로 구현)
            // 여기서는 간단한 데모만 구현
            if (!this.notifiedStocks.length) return;

            this.notifiedStocks.forEach(notification => {
                // 실제 구현에서는 서버에서 최신 하락률 정보를 가져와야 함
                if (notification.currentDrop >= notification.threshold) {
                    if (Notification && Notification.permission === 'granted') {
                        new Notification(`${notification.name} 알림`, {
                            body: `${notification.name}의 하락률이 ${notification.threshold}%에 도달했습니다.`,
                            icon: '/favicon.ico'
                        });
                    }
                }
            });
        },

        // 필터 영역 토글
        toggleFilterVisibility() {
            this.isFilterVisible = !this.isFilterVisible;
        },

        // 디바이스 타입 체크
        checkDeviceType() {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 768;

            // 모바일에서 데스크톱으로 전환 시 필터 항상 표시
            if (wasMobile && !this.isMobile) {
                this.isFilterVisible = true;
            }
            // 처음 로드 시 모바일이면 필터 숨기기, 데스크톱이면 표시
            else if (!wasMobile && this.isMobile) {
                this.isFilterVisible = false;
            }
        }
    },

    beforeUnmount() {
        window.removeEventListener('resize', this.checkDeviceType);
    }
};
</script>

<style>
@import '../assets/css/mainView.css';
@import '../assets/css/mobile-optimized-css.css';
</style>