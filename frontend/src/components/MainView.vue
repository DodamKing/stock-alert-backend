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

                <div class="market-filter">
                    <span>시장 필터:</span>
                    <label><input type="checkbox" v-model="markets.kospi"> 코스피</label>
                    <label><input type="checkbox" v-model="markets.kosdaq"> 코스닥</label>
                    <label><input type="checkbox" v-model="markets.us"> 미국</label>
                    <label><input type="checkbox" v-model="markets.etf"> ETF</label>
                    <button @click="saveUserPreferences" class="save-btn">저장</button>
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
export default {
    name: 'App',
    data() {
        return {
            searchQuery: '',
            searchResults: [],
            stockData: null,
            loading: false,
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
            notifyThreshold: 20,
            showNotifyOptions: false,
            hasNotification: false,
            notifiedStocks: []
        };
    },
    mounted() {
        // 사용자 설정 불러오기
        this.loadUserPreferences();

        // dropBar 애니메이션 설정
        this.$watch('stockData', (newVal) => {
            if (newVal) {
                // DOM 업데이트 후 실행
                this.$nextTick(() => {
                    if (this.$refs.dropBar) {
                        setTimeout(() => {
                            this.$refs.dropBar.style.width = Math.min(newVal.drop.percent, 100) + '%';
                        }, 100);
                    }
                });
            }
        });

        // 검색 입력란에 포커스
        this.$nextTick(() => {
            if (this.$refs.searchInput) {
                this.$refs.searchInput.focus();
            }
        });

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

        async getStockData(symbol, market) {
            this.loading = true;
            this.error = null;
            this.showNotifyOptions = false;

            try {
                const response = await fetch(
                    `${this.apiBaseUrl}/peak-drop?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}`
                );

                if (!response.ok) {
                    throw new Error('데이터를 가져오는 중 오류가 발생했습니다.');
                }

                const data = await response.json();

                if (data.status === 'success') {
                    this.stockData = data.data;

                    // 저장된 알림 설정이 있는지 확인
                    this.hasNotification = this.notifiedStocks.some(item =>
                        item.symbol === this.stockData.symbol
                    );
                } else {
                    throw new Error(data.message || '데이터를 가져오는 중 오류가 발생했습니다.');
                }
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        clearStockData() {
            this.stockData = null;
            this.showNotifyOptions = false;
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

        getDropClass(dropPercent) {
            if (dropPercent <= 0) return 'no-drop';
            if (dropPercent < 5) return 'minor-drop';
            if (dropPercent < 10) return 'small-drop';
            if (dropPercent < 20) return 'medium-drop';
            if (dropPercent < 30) return 'large-drop';
            return 'severe-drop';
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

        setNotification() {
            if (this.hasNotification) {
                // 이미 설정된 알림이 있으면 제거
                this.notifiedStocks = this.notifiedStocks.filter(item =>
                    item.symbol !== this.stockData.symbol
                );
                this.hasNotification = false;
                localStorage.setItem('notifiedStocks', JSON.stringify(this.notifiedStocks));
                this.showNotification('알림이 해제되었습니다.', 'info');
            } else {
                // 알림 설정 옵션 표시
                this.showNotifyOptions = !this.showNotifyOptions;
            }
        },

        saveNotification() {
            // 현재 종목 정보와 임계값을 저장
            const notification = {
                symbol: this.stockData.symbol,
                name: this.stockData.name,
                market: this.stockData.market,
                threshold: this.notifyThreshold,
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
            this.showNotifyOptions = false;
            this.showNotification('알림이 설정되었습니다.', 'success');

            // 알림 권한 요청
            if (Notification && Notification.permission !== 'granted') {
                Notification.requestPermission();
            }
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
        }
    }
};
</script>

<style>
@import '../assets/css/mainView.css'
</style>