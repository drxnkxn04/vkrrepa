// frontend/src/services/api.js

import axios from 'axios';

// Базовый URL для API (измените на ваш production URL при деплое)
const BASE_URL = process.env.VUE_APP_API_URL || 'http://127.0.0.1:8000';

// Создание экземпляра axios с базовой конфигурацией
const apiClient = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 секунд таймаут
});

// Interceptor для добавления токена к каждому запросу
apiClient.interceptors.request.use(
  (config) => {
    // Получаем токен из localStorage
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
    
    // Если получили 401 и это не повторный запрос
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Пытаемся обновить токен
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
          const response = await axios.post(`${BASE_URL}/api/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          
          // Сохраняем новый токен
          localStorage.setItem('access_token', access);
          
          // Повторяем оригинальный запрос с новым токеном
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Если обновление токена не удалось, перенаправляем на логин
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Перенаправление на страницу логина
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
  // Вход в систему
  login(username, password) {
    return axios.post(`${BASE_URL}/api/token/`, {
      username,
      password,
    });
  },
  
  // Обновление токена
  refreshToken(refreshToken) {
    return axios.post(`${BASE_URL}/api/token/refresh/`, {
      refresh: refreshToken,
    });
  },
  
  // Выход из системы (очистка токенов на клиенте)
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
  
  // История KPI
  getHistory(months = 6) {
    return apiClient.get('/kpi/values/history/', {
      params: { months },
    });
  },
  
  // Рекомендации
  getRecommendations(period) {
    return apiClient.get('/kpi/values/recommendations/', {
      params: { period },
    });
  },
  
  // Доступные периоды
  getPeriods() {
    return apiClient.get('/kpi/values/periods/');
  },
  
  // === Работа со значениями KPI ===
  getValues() {
    return apiClient.get('/kpi/values/');
  },
  
  createValue(data) {
    // Если есть файл, используем FormData
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
    return apiClient.patch(`/kpi/values/${id}/`, data);
  },
  
  deleteValue(id) {
    return apiClient.delete(`/kpi/values/${id}/`);
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
  
  // === Отчеты ===
  generateReport(period) {
    return apiClient.get('/kpi/reports/generate/', {
      params: { period },
      responseType: 'blob', // Для скачивания файла
    });
  },
  
  // === Интеграции ===
  syncCrossref(data) {
    return apiClient.post('/kpi/crossref/sync/', data);
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

// Экспорт основного клиента
export default apiClient;