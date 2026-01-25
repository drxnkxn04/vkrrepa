// frontend/src/main.js

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import apiClient from './services/api';
import Toast from "vue-toastification";
import "vue-toastification/dist/index.css";

// Импорт глобальных стилей (если есть)
// import './assets/styles/main.css';

// Создание экземпляра Vue приложения
const app = createApp(App);

// Глобальное свойство для API (доступно через this.$api в компонентах)
app.config.globalProperties.$api = apiClient;

// Простая реализация toast-уведомлений
const toast = {
  success(message) {
    console.log('✅ SUCCESS:', message);
    // Можно заменить на любую библиотеку уведомлений
    // Например: vue-toastification, vue-toast-notification и т.д.
    alert(`✅ ${message}`);
  },
  
  error(message) {
    console.error('❌ ERROR:', message);
    alert(`❌ ${message}`);
  },
  
  info(message) {
    console.info('ℹ️ INFO:', message);
    alert(`ℹ️ ${message}`);
  },
  
  warning(message) {
    console.warn('⚠️ WARNING:', message);
    alert(`⚠️ ${message}`);
  },
};

// Глобальное свойство для уведомлений
app.config.globalProperties.$toast = toast;

// Глобальный обработчик ошибок
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error handler:', err);
  console.error('Component:', instance);
  console.error('Error info:', info);
  
  // Показываем уведомление пользователю
  toast.error('Произошла ошибка. Пожалуйста, попробуйте еще раз.');
};

// Использование плагинов
app.use(store);
app.use(router);

app.use(Toast, {
  timeout: 3000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: "button",
  icon: true,
  rtl: false
});

// Монтирование приложения
app.mount('#app');

// Экспорт для использования в других модулях
export { toast };