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
  if (process.env.NODE_ENV !== 'production') {
    console.error('Global error handler:', err, info);
  }
  app.config.globalProperties.$toast.error('Произошла ошибка. Пожалуйста, попробуйте еще раз.');
};

app.use(store);
app.use(router);

app.mount('#app');

export { toastPlugin };