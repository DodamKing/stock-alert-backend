import { createRouter, createWebHistory } from 'vue-router'
import MainView from '../views/MainView.vue'
import BacktestView from '../views/BacktestView.vue'

const routes = [
    {
        path: '/',
        name: 'home',
        component: MainView
    },
    {
        path: '/backtest',
        name: 'backtest',
        component: BacktestView
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router