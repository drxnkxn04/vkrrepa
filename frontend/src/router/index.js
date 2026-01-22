import { createRouter, createWebHistory } from 'vue-router';
import store from '../store';
import Login from '../views/Login.vue';
import Dashboard from '../views/Dashboard.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guest: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  // Здесь будут другие страницы, например, /history, /recommendations
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

// Навигационный страж: защищает роуты, требующие аутентификации
router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!store.getters.isAuthenticated) {
      next({ name: 'Login' });
    } else {
      next();
    }
  } else if (to.matched.some(record => record.meta.guest)) {
    if (store.getters.isAuthenticated) {
      next({ name: 'Dashboard' });
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router;
