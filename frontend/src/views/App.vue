<template>
    <div id="app-container">
      <header v-if="isAuthenticated" class="app-header">
        <div class="logo">Система KPI</div>
        <nav class="navigation">
          <router-link to="/">Дашборд</router-link>
          <!-- Ссылки на будущие страницы -->
          <!-- <router-link to="/history">История</router-link> -->
          <!-- <router-link to="/input">Ввод данных</router-link> -->
        </nav>
        <div class="user-menu">
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
      ...mapGetters(['isAuthenticated'])
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
  /* Стили из вашего Dashboard.vue, которые полезно сделать глобальными */
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
  .navigation a { margin: 0 16px; text-decoration: none; color: #555; font-weight: 500; }
  .navigation a.router-link-exact-active { color: #007bff; }
  .logout-button { background: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
  .app-content {
    padding: 24px;
  }
  </style>
  