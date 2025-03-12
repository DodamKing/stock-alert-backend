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
            <p>데이터 제공: FinanceDataReader | © 2025 주식 전고점 대비 하락률 조회 서비스</p>
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
:root {
    /* 라이트 모드 색상 */
    --primary-color: #3b82f6;
    --secondary-color: #60a5fa;
    --accent-color: #f97316;
    --background-color: #f8fafc;
    --card-color: #ffffff;
    --text-color: #334155;
    --border-color: #e2e8f0;
    --hover-color: #f1f5f9;

    --no-drop-color: #10b981;
    --minor-drop-color: #84cc16;
    --small-drop-color: #facc15;
    --medium-drop-color: #f97316;
    --large-drop-color: #ef4444;
    --severe-drop-color: #b91c1c;
}

.dark-mode {
    /* 다크 모드 색상 */
    --primary-color: #60a5fa;
    --secondary-color: #3b82f6;
    --accent-color: #fb923c;
    --background-color: #0f172a;
    --card-color: #1e293b;
    --text-color: #e2e8f0;
    --border-color: #334155;
    --hover-color: #1e293b;

    --no-drop-color: #059669;
    --minor-drop-color: #65a30d;
    --small-drop-color: #ca8a04;
    --medium-drop-color: #ea580c;
    --large-drop-color: #dc2626;
    --severe-drop-color: #991b1b;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    transition: background-color 0.3s, color 0.3s, border-color 0.3s;
}

body {
    font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
    line-height: 1.6;
}

.app-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
    min-height: 100vh;
}

header {
    text-align: center;
    margin-bottom: 30px;
    position: relative;
}

header h1 {
    color: var(--primary-color);
    margin-bottom: 10px;
    font-weight: 700;
}

.subtitle {
    color: var(--text-color);
    opacity: 0.7;
    font-size: 1.1rem;
}

.theme-toggle {
    position: absolute;
    top: 0;
    right: 0;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 10px;
    border-radius: 50%;
    transition: transform 0.3s;
}

.theme-toggle:hover {
    transform: rotate(15deg);
}

.search-container {
    background-color: var(--card-color);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
    border: 1px solid var(--border-color);
}

.search-box {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
}

.search-box input {
    flex: 1;
    padding: 12px 15px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    font-size: 1rem;
    background-color: var(--background-color);
    color: var(--text-color);
    outline: none;
    transition: all 0.3s;
}

.search-box input:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.search-box button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0 20px;
    cursor: pointer;
    font-weight: 500;
    font-size: 1rem;
    transition: all 0.3s;
}

.search-box button:hover {
    background-color: var(--secondary-color);
    transform: translateY(-2px);
}

.search-box button:disabled {
    background-color: var(--border-color);
    cursor: not-allowed;
    transform: none;
}

.pulse-on-hover:hover:not(:disabled) {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
    }

    70% {
        box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
    }

    100% {
        box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
    }
}

.market-filter {
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
}

.market-filter span {
    font-weight: 500;
    color: var(--text-color);
    opacity: 0.7;
}

.market-filter label {
    display: flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
}

.save-btn {
    background-color: var(--secondary-color);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 0.8rem;
    margin-left: auto;
    transition: all 0.3s;
}

.save-btn:hover {
    background-color: var(--primary-color);
}

.loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 0;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(59, 130, 246, 0.2);
    border-radius: 50%;
    border-top-color: var(--primary-color);
    animation: spin 1s ease-in-out infinite;
    margin-bottom: 15px;
}

.spinner-small {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.search-results,
.stock-detail {
    background-color: var(--card-color);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
    border: 1px solid var(--border-color);
}

.search-results h2,
.stock-detail h2 {
    color: var(--primary-color);
    margin-bottom: 15px;
    font-weight: 600;
}

.results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
    margin-top: 15px;
}

.stock-item {
    background-color: var(--background-color);
    border-radius: 8px;
    padding: 15px;
    cursor: pointer;
    transition: all 0.3s;
    border: 1px solid var(--border-color);
    animation: fadeIn 0.5s ease-out forwards;
    opacity: 0;
}

.stock-item:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    border-color: var(--primary-color);
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

.stock-name {
    font-weight: 600;
    margin-bottom: 5px;
}

.stock-symbol {
    color: var(--text-color);
    opacity: 0.7;
    font-size: 0.9rem;
    margin-bottom: 8px;
}

.stock-market {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
    color: white;
}

.kr-stock {
    background-color: var(--primary-color);
}

.us-stock {
    background-color: #8b5cf6;
}

.etf {
    background-color: #10b981;
}

.back-button {
    display: inline-block;
    margin-bottom: 20px;
    color: var(--primary-color);
    cursor: pointer;
    font-weight: 500;
    position: relative;
    overflow: hidden;
    padding: 5px 10px;
    border-radius: 4px;
}

.back-button:hover {
    background-color: var(--hover-color);
}

.ripple {
    position: relative;
    overflow: hidden;
}

.ripple::after {
    content: "";
    display: block;
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    pointer-events: none;
    background-image: radial-gradient(circle, rgba(255, 255, 255, 0.2) 10%, transparent 10.01%);
    background-repeat: no-repeat;
    background-position: 50%;
    transform: scale(10, 10);
    opacity: 0;
    transition: transform 0.5s, opacity 1s;
}

.ripple:active::after {
    transform: scale(0, 0);
    opacity: 0.3;
    transition: 0s;
}

.stock-header {
    margin-bottom: 20px;
}

.stock-meta {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-top: 5px;
}

.price-container {
    display: flex;
    gap: 20px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}

.current-price,
.peak-price {
    flex: 1;
    min-width: 200px;
    padding: 15px;
    background-color: var(--background-color);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.label {
    font-size: 0.9rem;
    color: var(--text-color);
    opacity: 0.7;
    margin-bottom: 5px;
}

.value {
    font-size: 1.8rem;
    font-weight: 600;
}

.drop-container {
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

.notify-options select {
    width: 100%;
    padding: 8px;
    margin: 10px 0;
    border-radius: 4px;
    border: 1px solid var(--border-color);
    background-color: var(--card-color);
    color: var(--text-color);
}

.save-notify-btn {
    background-color: var(--accent-color);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s;
}

.save-notify-btn:hover {
    background-color: #ea580c;
}

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

.other-matches h3 {
    margin-bottom: 15px;
    font-weight: 600;
    color: var(--primary-color);
}

.last-update {
    color: var(--text-color);
    opacity: 0.6;
    font-size: 0.9rem;
    text-align: right;
    margin-top: 10px;
}

.error-message {
    background-color: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
    text-align: center;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.notification-toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 8px;
    background-color: var(--card-color);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    max-width: 300px;
    animation: slideInRight 0.3s ease-out;
}

.notification-toast.success {
    border-left: 4px solid var(--no-drop-color);
}

.notification-toast.warning {
    border-left: 4px solid var(--small-drop-color);
}

.notification-toast.error {
    border-left: 4px solid var(--severe-drop-color);
}

.notification-toast.info {
    border-left: 4px solid var(--primary-color);
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }

    to {
        transform: translateX(0);
        opacity: 1;
    }
}

footer {
    text-align: center;
    padding: 20px 0;
    color: var(--text-color);
    opacity: 0.6;
    font-size: 0.9rem;
    margin-top: 40px;
}

/* 애니메이션 클래스 */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.5s;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
    transition: all 0.5s;
}

.slide-up-enter-from,
.slide-up-leave-to {
    opacity: 0;
    transform: translateY(30px);
}

.slide-right-enter-active,
.slide-right-leave-active {
    transition: all 0.5s;
}

.slide-right-enter-from,
.slide-right-leave-to {
    opacity: 0;
    transform: translateX(30px);
}

.slide-down-enter-active,
.slide-down-leave-active {
    transition: all 0.5s;
}

.slide-down-enter-from,
.slide-down-leave-to {
    opacity: 0;
    transform: translateY(-20px);
}

.list-enter-active,
.list-leave-active {
    transition: all 0.5s;
}

.list-enter-from,
.list-leave-to {
    opacity: 0;
    transform: translateY(30px);
}

.toast-enter-active,
.toast-leave-active {
    transition: all 0.3s;
}

.toast-enter-from,
.toast-leave-to {
    opacity: 0;
    transform: translateY(20px);
}

/* 반응형 디자인 */
@media (max-width: 768px) {
    .app-container {
        padding: 10px;
    }

    .search-box {
        flex-direction: column;
    }

    .search-box button {
        padding: 12px;
    }

    .market-filter {
        flex-direction: column;
        align-items: flex-start;
    }

    .market-filter span {
        margin-bottom: 10px;
    }

    .save-btn {
        margin-left: 0;
        margin-top: 10px;
        width: 100%;
        padding: 8px;
    }

    .price-container {
        flex-direction: column;
        gap: 10px;
    }

    .drop-header,
    .drop-values {
        flex-direction: column;
        align-items: flex-start;
        gap: 5px;
    }

    .results-grid {
        grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
    }

    .stock-item:hover {
        transform: none;
    }

    .notification-toast {
        left: 10px;
        right: 10px;
        max-width: none;
    }
}

/* 다크 모드에서의 입력 요소 스타일 */
.dark-mode input[type="text"],
.dark-mode input[type="number"],
.dark-mode select {
    background-color: #1e293b;
    color: #e2e8f0;
    border-color: #334155;
}

.dark-mode input[type="text"]:focus,
.dark-mode input[type="number"]:focus,
.dark-mode select:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
}
</style>