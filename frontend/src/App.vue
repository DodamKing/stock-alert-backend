<template>
  <div>
    <nav class="main-nav">
      <div class="nav-container">
        <router-link to="/" class="nav-logo">주식 분석</router-link>
        <div class="nav-links">
          <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
            <span class="icon">📊</span> 하락률 조회
          </router-link>
          <router-link to="/backtest" class="nav-link" :class="{ active: $route.path === '/backtest' }">
            <span class="icon">🔍</span> 백테스팅
          </router-link>
        </div>
      </div>
    </nav>

    <router-view />

    <Adsense />
  </div>
</template>

<script>
import AdSense from './components/AdSense.vue';
export default {
  name: 'App',
  components: {
    AdSense
  }
}
</script>

<style>
.main-nav {
  background-color: var(--card-color);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
}

.nav-logo {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--primary-color);
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.nav-link {
  text-decoration: none;
  color: var(--text-color);
  padding: 8px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  transition: all 0.3s;
}

.nav-link .icon {
  margin-right: 6px;
}

.nav-link:hover,
.nav-link.active {
  background-color: var(--background-color);
  color: var(--primary-color);
}

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 10px;
  }

  .nav-links {
    width: 100%;
    justify-content: space-around;
  }

  .nav-link {
    font-size: 0.9rem;
    padding: 8px;
  }
}
</style>