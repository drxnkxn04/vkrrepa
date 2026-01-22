
import { createApp } from 'vue'
import App from './views/App.vue' // 
import router from './router'
import store from './store'
import api from './services/api' // Импортируем наш api сервис

const app = createApp(App);

// "Инъекция" API-клиента, чтобы его можно было использовать как this.$api
app.config.globalProperties.$api = api;

// Простой мок-объект для уведомлений, чтобы код не ломался
app.config.globalProperties.$toast = {
    info: (msg) => console.log('INFO:', msg),
    success: (msg) => console.log('SUCCESS:', msg),
    error: (msg) => console.error('ERROR:', msg),
};

app.use(store);
app.use(router);

app.mount('#app');
