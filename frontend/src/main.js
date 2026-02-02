import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import apiClient from './services/api';
import toastPlugin from './plugins/toast'; // НОВЫЙ ИМПОРТ

const app = createApp(App);

app.config.globalProperties.$api = apiClient;

// ЗАМЕНИТЬ vue-toastification на наш плагин
app.use(toastPlugin);

// Глобальный обработчик ошибок
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error handler:', err);
  console.error('Component:', instance);
  console.error('Error info:', info);
  
  // Используем наш toast
  app.config.globalProperties.$toast.error('Произошла ошибка. Пожалуйста, попробуйте еще раз.');
};

app.use(store);
app.use(router);

app.mount('#app');

export { toastPlugin };