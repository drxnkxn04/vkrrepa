import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api', // ПРАВИЛЬНО для конфигурации с Nginx
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Этот перехватчик будет добавлять токен в заголовок каждого запроса
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

export default apiClient;
