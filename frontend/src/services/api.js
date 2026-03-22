// frontend/src/services/api.js

import axios from 'axios';

// Базовый URL для API
const BASE_URL = process.env.VUE_APP_API_URL || 'http://127.0.0.1:8000';

// Создание экземпляра axios с базовой конфигурацией
const apiClient = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Interceptor для добавления токена к каждому запросу
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor для обработки ответов и автоматического обновления токена
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
          const response = await axios.post(`${BASE_URL}/api/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// API методы для работы с аутентификацией
export const authAPI = {
  login(username, password) {
    return axios.post(`${BASE_URL}/api/token/`, {
      username,
      password,
    });
  },
  
  refreshToken(refreshToken) {
    return axios.post(`${BASE_URL}/api/token/refresh/`, {
      refresh: refreshToken,
    });
  },
  
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return Promise.resolve();
  },
};

// API методы для работы с KPI
export const kpiAPI = {
  // === Дашборд ===
  getDashboard(period) {
    return apiClient.get('/kpi/values/dashboard/', {
      params: { period },
    });
  },
  
  getHistory(months = 6) {
    return apiClient.get('/kpi/values/history/', {
      params: { months },
    });
  },
  
  getRecommendations(period) {
    return apiClient.get('/kpi/values/recommendations/', {
      params: { period },
    });
  },
  
  getPeriods() {
    return apiClient.get('/kpi/values/periods/');
  },
  
  // === Работа со значениями KPI ===
  getValues() {
    return apiClient.get('/kpi/values/');
  },

  getValuesByParams(params) {
    return apiClient.get('/kpi/values/', { params });
  },
  
  createValue(data) {
    if (data.evidence instanceof File) {
      const formData = new FormData();
      formData.append('indicator_id', data.indicator_id);
      formData.append('period', data.period);
      formData.append('actual_value', data.actual_value);
      formData.append('comment', data.comment || '');
      formData.append('evidence', data.evidence);
      
      return apiClient.post('/kpi/values/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    }
    
    return apiClient.post('/kpi/values/', data);
  },
  
  updateValue(id, data) {
    const isFormData = data instanceof FormData;
    return apiClient.patch(`/kpi/values/${id}/`, data, {
      headers: isFormData ? { 'Content-Type': 'multipart/form-data' } : {},
    });
  },
  
  deleteValue(id) {
    return apiClient.delete(`/kpi/values/${id}/`);
  },

  submitValue(id) {
    return apiClient.post(`/kpi/values/${id}/submit/`);
  },

  approveValue(id, review_comment) {
    return apiClient.post(`/kpi/values/${id}/approve/`, { review_comment });
  },

  rejectValue(id, review_comment) {
    return apiClient.post(`/kpi/values/${id}/reject/`, { review_comment });
  },

  getPendingValues(period) {
    return apiClient.get('/kpi/values/pending/', {
      params: period ? { period } : {},
    });
  },
  
  // === Справочники ===
  getGroups() {
    return apiClient.get('/kpi/groups/');
  },
  
  getManualIndicators() {
    return apiClient.get('/kpi/indicators/manual/');
  },
  
  // === Рекомендации ===
  getRecommendationsList() {
    return apiClient.get('/kpi/recommendations-list/');
  },
  
  completeRecommendation(id) {
    return apiClient.post(`/kpi/recommendations-list/${id}/complete/`);
  },
  
  // === Профиль пользователя ===
  getProfile() {
    return apiClient.get('/kpi/profile/');
  },
  
  updateProfile(data) {
    return apiClient.patch('/kpi/profile/', data);
  },
  
  // === Отчеты ===
  generateReport(period) {
    return apiClient.get('/kpi/reports/generate/', {
      params: { period },
      responseType: 'blob',
    });
  },

  generateUserReport(userId, period) {
    return apiClient.get(`/kpi/reports/generate/${userId}/`, {
      params: { period },
      responseType: 'blob',
    });
  },

  generateExcelReport(period) {
    return apiClient.get('/kpi/reports/generate-excel/', {
      params: { period },
      responseType: 'blob',
    });
  },

  generateUserExcelReport(userId, period) {
    return apiClient.get(`/kpi/reports/generate-excel/${userId}/`, {
      params: { period },
      responseType: 'blob',
    });
  },
  
  // === Интеграции ===
  syncCrossref(data) {
    return apiClient.post('/kpi/crossref/sync/', data);
  },
  
  // === Уведомления ===
  getNotifications() {
    return apiClient.get('/kpi/notifications/');
  },

  getUnreadCount() {
    return apiClient.get('/kpi/notifications/unread_count/');
  },

  markNotificationRead(id) {
    return apiClient.post(`/kpi/notifications/${id}/read/`);
  },

  markAllRead() {
    return apiClient.post('/kpi/notifications/read_all/');
  },

  // === Для руководителей ===
  getManagerDashboard(period) {
    return apiClient.get('/kpi/manager-dashboard/', {
      params: { period },
    });
  },
  
  getTopPerformers(period, limit = 10) {
    return apiClient.get('/kpi/top-performers/', {
      params: { period, limit },
    });
  },
};

// Вспомогательная функция для скачивания PDF
export const downloadPDF = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export default apiClient;
