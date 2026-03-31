// frontend/src/store/index.js

import { createStore } from 'vuex';
import { authAPI, kpiAPI } from '../services/api';
import router from '../router';

// Vuex Store для управления глобальным состоянием приложения
const store = createStore({
  state: {
    // Состояние аутентификации
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    authStatus: '', // 'loading', 'success', 'error'
    
    // Данные KPI
    currentPeriod: null,
    dashboardData: null,
    
    // Кэш справочников
    manualIndicators: null,

    // UI состояние
    loading: false,
    error: null,
  },
  
  getters: {
    // Проверка, авторизован ли пользователь
    isAuthenticated: (state) => {
      return !!state.accessToken;
    },
    
    // Проверка, является ли пользователь администратором
    isAdmin: (state) => {
      return state.user?.is_staff === true || state.user?.is_superuser === true;
    },
    
    // Получение текущего пользователя
    currentUser: (state) => {
      return state.user;
    },
    
    // Статус аутентификации
    authStatus: (state) => {
      return state.authStatus;
    },
    
    // Данные дашборда
    dashboardData: (state) => {
      return state.dashboardData;
    },
    
    // Текущий период
    currentPeriod: (state) => {
      if (state.currentPeriod) {
        return state.currentPeriod;
      }
      // Возвращаем текущий месяц по умолчанию
      const now = new Date();
      return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    },
    
    // Состояние загрузки
    isLoading: (state) => {
      return state.loading;
    },
    
    // Ошибка
    error: (state) => {
      return state.error;
    },
  },
  
  mutations: {
    // Установка токенов
    SET_TOKENS(state, { access, refresh }) {
      state.accessToken = access;
      state.refreshToken = refresh;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
    },
    
    // Установка данных пользователя
    SET_USER(state, user) {
      state.user = user;
      localStorage.setItem('user', JSON.stringify(user));
    },
    
    // Очистка данных аутентификации
    CLEAR_AUTH(state) {
      state.accessToken = null;
      state.refreshToken = null;
      state.user = null;
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    },
    
    // Установка статуса аутентификации
    SET_AUTH_STATUS(state, status) {
      state.authStatus = status;
    },
    
    // Установка данных дашборда
    SET_DASHBOARD_DATA(state, data) {
      state.dashboardData = data;
    },
    
    // Установка текущего периода
    SET_CURRENT_PERIOD(state, period) {
      state.currentPeriod = period;
    },
    
    // Установка состояния загрузки
    SET_LOADING(state, loading) {
      state.loading = loading;
    },
    
    // Установка ошибки
    SET_ERROR(state, error) {
      state.error = error;
    },
    
    // Очистка ошибки
    CLEAR_ERROR(state) {
      state.error = null;
    },

    // Кэш индикаторов
    SET_MANUAL_INDICATORS(state, indicators) {
      state.manualIndicators = indicators;
    },
  },
  
  actions: {
    // Вход в систему
    async login({ commit }, { username, password }) {
      commit('SET_AUTH_STATUS', 'loading');
      commit('CLEAR_ERROR');
      
      try {
        const response = await authAPI.login(username, password);
        const { access, refresh } = response.data;
        
        commit('SET_TOKENS', { access, refresh });
        
        const payload = JSON.parse(atob(access.split('.')[1]));

        const user = {
          id: payload.user_id,
          username: username,
          is_staff: payload.is_staff || false,
          is_superuser: payload.is_superuser || false,
          email: payload.email || '',
          full_name: payload.full_name || username
        };
        
        commit('SET_USER', user);
        commit('SET_AUTH_STATUS', 'success');
        
        // Перенаправляем на сохранённый путь или на главную
        const redirect = router.currentRoute.value.query.redirect;
        const safePath = (typeof redirect === 'string' && redirect.startsWith('/')) ? redirect : '/';
        router.push(safePath);

        return { success: true };
      } catch (error) {
        console.error('Login error:', error);
        commit('SET_AUTH_STATUS', 'error');
        commit('SET_ERROR', error.response?.data?.detail || 'Ошибка входа в систему');
        throw error;
      }
    },
    
    // Выход из системы
    async logout({ commit }) {
      try {
        await authAPI.logout();
      } catch (error) {
        console.error('Logout error:', error);
      } finally {
        commit('CLEAR_AUTH');
        commit('SET_DASHBOARD_DATA', null);
        router.push('/login');
      }
    },
    
    // Обновление токена
    async refreshToken({ commit, state }) {
      try {
        const response = await authAPI.refreshToken(state.refreshToken);
        const { access } = response.data;
        
        commit('SET_TOKENS', { 
          access, 
          refresh: state.refreshToken 
        });
        
        return { success: true };
      } catch (error) {
        console.error('Token refresh error:', error);
        // Если обновление токена не удалось, выходим из системы
        commit('CLEAR_AUTH');
        router.push('/login');
        throw error;
      }
    },
    
    // Загрузка данных дашборда
    async loadDashboard({ commit, getters }, period) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      
      try {
        const targetPeriod = period || getters.currentPeriod;
        
        // Импортируем API здесь, чтобы избежать циклических зависимостей
        const { kpiAPI } = await import('../services/api');
        const response = await kpiAPI.getDashboard(targetPeriod);
        
        commit('SET_DASHBOARD_DATA', response.data);
        commit('SET_CURRENT_PERIOD', targetPeriod);
        
        return response.data;
      } catch (error) {
        console.error('Dashboard load error:', error);
        commit('SET_ERROR', 'Не удалось загрузить данные дашборда');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    // Загрузка и кэширование индикаторов для ручного ввода
    async loadManualIndicators({ commit, state }) {
      if (state.manualIndicators) return state.manualIndicators;
      const response = await kpiAPI.getManualIndicators();
      commit('SET_MANUAL_INDICATORS', response.data);
      return response.data;
    },

    // Очистка ошибки
    clearError({ commit }) {
      commit('CLEAR_ERROR');
    },
  },
  
  modules: {
    // Здесь можно добавить дополнительные модули для разделения логики
    // Например: kpi, recommendations, reports и т.д.
  },
});

export default store;