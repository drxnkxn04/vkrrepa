// frontend/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import store from '../store';

// Импорт компонентов-представлений
import Login from '../views/Login.vue';
import Dashboard from '../views/Dashboard.vue';
import History from '../views/History.vue';
import ManagerDashboard from '../views/ManagerDashboard.vue';
import Recommendations from '../views/Recommendations.vue';
import Profile from '../views/Profile.vue';
import NotFound from '../views/NotFound.vue';

// Определение маршрутов
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      requiresAuth: false,
      title: 'Вход в систему',
    },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      requiresAuth: true,
      title: 'Дашборд KPI',
    },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue'), // Lazy loading
    meta: {
      requiresAuth: true,
      title: 'История KPI',
    },
  },
  {
    path: '/manager',
    name: 'ManagerDashboard',
    component: () => import('../views/ManagerDashboard.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true, // Только для администраторов
      title: 'Дашборд руководителя',
    },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: {
      requiresAuth: true,
      title: 'Профиль',
    },
  },
  {
    path: '/recommendations',
    name: 'Recommendations',
    component: () => import('../views/Recommendations.vue'),
    meta: {
      requiresAuth: true,
      title: 'Рекомендации',
    },
  },
  // Страница 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: {
      title: 'Страница не найдена',
    },
  },
  {
    path: '/crossref-import',
    name: 'CrossrefImport',
    component: () => import('../components/CrossrefImport.vue'),
    meta: {
      requiresAuth: true,
      title: 'Импорт публикаций из Crossref',
    },
  }
];

// Создание экземпляра роутера
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  // Прокрутка к началу страницы при навигации
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0 };
    }
  },
});

// Navigation Guard - проверка аутентификации перед каждым переходом
router.beforeEach((to, from, next) => {
  // Установка заголовка страницы
  document.title = to.meta.title || 'KPI System';
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);
  const isAuthenticated = store.getters.isAuthenticated;
  const isAdmin = store.getters.isAdmin;

  // Если маршрут требует аутентификации
  if (requiresAuth) {
    if (!isAuthenticated) {
      // Пользователь не авторизован - перенаправляем на логин
      next({
        name: 'Login',
        query: { redirect: to.fullPath }, // Сохраняем куда хотел перейти
      });
    } else if (requiresAdmin && !isAdmin) {
      // Пользователь авторизован, но не админ


      next({ name: 'Dashboard' }); // Перенаправляем на главную
    } else {
      // Все проверки пройдены
      next();
    }
  } else {
    // Маршрут не требует аутентификации
    if (to.name === 'Login' && isAuthenticated) {
      // Если пользователь уже авторизован и пытается зайти на логин
      next({ name: 'Dashboard' });
    } else {
      next();
    }
  }
});

// Обработка ошибок навигации
router.onError((error) => {
  console.error('Router error:', error);
});

export default router;