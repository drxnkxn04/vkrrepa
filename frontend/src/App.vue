<!-- frontend/src/views/App.vue -->
<template>
  <div id="app-container">
    <header v-if="isAuthenticated" class="app-header">
      <div class="logo">Система KPI</div>
      
      <nav class="navigation">
        <router-link to="/">Дашборд</router-link>
        <router-link to="/history">История</router-link>
        <router-link to="/recommendations">Рекомендации</router-link>
        <router-link to="/crossref-import"> Импорт публикаций</router-link>
        <router-link v-if="isAdmin" to="/manager" class="admin-link"> Управление</router-link>
        <span style="color: red; font-size: 10px;">
  </span>
      </nav>

      <div class="user-menu">
        <router-link to="/profile" class="profile-info">
          <span class="user-avatar">{{ userInitials }}</span>
          <span class="user-name">{{ currentUser?.username }}</span>
        </router-link>
        <button @click="handleLogout" class="logout-button">Выйти</button>
      </div>
    </header>

    <main class="app-content">
      <router-view/>
    </main>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'App',
  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin', 'currentUser']),
    userInitials() {
      const name = this.currentUser?.full_name || this.currentUser?.username || 'U';
      return name
        .split(' ')
        .map(word => word[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
  },
  methods: {
    ...mapActions(['logout']),
    handleLogout() {
      this.logout();
    }
  }
}
</script>

<style>
/* Добавьте стили для user-menu */
.user-menu {
  display: flex;
  align-items: center;
  gap: 16px;
}

.profile-link {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: #555;
  padding: 6px 12px;
  border-radius: 20px;
  transition: background 0.2s;
}

.profile-link:hover {
  background: #f8f9fa;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.85rem;
}

.user-name {
  font-weight: 500;
}
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #f4f7f6;
  color: #333;
}
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  height: 64px;
}
.logo { font-weight: bold; font-size: 1.5rem; }
.navigation a { 
  margin: 0 16px; 
  text-decoration: none; 
  color: #555; 
  font-weight: 500;
  transition: color 0.2s;
}
.navigation a:hover { color: #007bff; }
.navigation a.router-link-exact-active { color: #007bff; }
.user-menu {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-name {
  font-weight: 500;
  color: #555;
}
.logout-button { 
  background: #dc3545; 
  color: white; 
  border: none; 
  padding: 8px 16px; 
  border-radius: 4px; 
  cursor: pointer;
  transition: opacity 0.2s;
}
.logout-button:hover {
  opacity: 0.9;
}
.app-content {
  padding: 24px;
}

.navigation .admin-link {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
}

.navigation .admin-link:hover {
  opacity: 0.9;
  color: white !important;
}
</style>