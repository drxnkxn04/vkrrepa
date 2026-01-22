import { createStore } from 'vuex';
import api from '../services/api';
import router from '../router';

export default createStore({
  state: {
    token: localStorage.getItem('token') || '',
    status: '',
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem('token', token);
    },
    SET_STATUS(state, status) {
      state.status = status;
    },
    LOGOUT(state) {
      state.token = '';
      localStorage.removeItem('token');
    }
  },
  actions: {
    async login({ commit }, credentials) {
      commit('SET_STATUS', 'loading');
      try {
        // Django Simple-JWT ожидает POST запрос на /token/
        const response = await api.post('/token/', credentials);
        const token = response.data.access;
        
        commit('SET_TOKEN', token);
        commit('SET_STATUS', 'success');
        
        await router.push('/');
      } catch (error) {
        commit('SET_STATUS', 'error');
        commit('LOGOUT');
        console.error("Ошибка аутентификации:", error);
        // Можно выбросить ошибку, чтобы компонент ее поймал
        throw error;
      }
    },
    logout({ commit }) {
      commit('LOGOUT');
      router.push('/login');
    }
  },
  getters: {
    isAuthenticated: state => !!state.token,
    authStatus: state => state.status,
  }
});
