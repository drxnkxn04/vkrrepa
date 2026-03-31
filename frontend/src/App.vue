<!-- frontend/src/views/App.vue -->
<template>
  <div id="app-container">
    <header v-if="isAuthenticated" class="app-header">
      <div class="logo">Система KPI</div>

      <nav class="navigation" aria-label="Основная навигация">
        <router-link to="/">Дашборд</router-link>
        <router-link to="/history">История</router-link>
        <router-link to="/recommendations">Рекомендации</router-link>
        <router-link to="/crossref-import">Импорт публикаций</router-link>
        <router-link v-if="isAdmin" to="/manager" class="admin-link"> Управление</router-link>
      </nav>

      <div class="user-menu">
        <!-- Колокольчик уведомлений -->
        <div class="notification-bell" ref="bellRef">
          <button class="bell-button" @click="toggleNotifications" aria-label="Уведомления" :aria-expanded="showNotifications">
            <span class="bell-icon" aria-hidden="true">&#128276;</span>
            <span v-if="unreadCount > 0" class="bell-badge" aria-label="Непрочитанных: {{ unreadCount }}">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </button>

          <div v-if="showNotifications" class="notification-dropdown" role="region" aria-label="Уведомления">
            <div class="notification-header">
              <span>Уведомления</span>
              <button v-if="unreadCount > 0" class="read-all-btn" @click="handleMarkAllRead">
                Прочитать все
              </button>
            </div>
            <div class="notification-list">
              <div
                v-for="notif in notifications"
                :key="notif.id"
                class="notification-item"
                :class="{ unread: !notif.is_read }"
                @click="handleMarkRead(notif)"
              >
                <div class="notif-icon" :class="notif.notification_type">
                  {{ notifIcon(notif.notification_type) }}
                </div>
                <div class="notif-body">
                  <div class="notif-title">{{ notif.title }}</div>
                  <div class="notif-message">{{ notif.message }}</div>
                  <div class="notif-time">{{ formatTime(notif.created_at) }}</div>
                </div>
              </div>
              <div v-if="notifications.length === 0" class="notification-empty">
                Нет уведомлений
              </div>
            </div>
          </div>
        </div>

        <router-link to="/profile" class="profile-info">
          <span class="user-avatar">{{ userInitials }}</span>
          <span class="user-name">{{ currentUser?.username }}</span>
        </router-link>
        <button @click="handleLogout" class="logout-button" aria-label="Выйти из системы">Выйти</button>
      </div>
    </header>

    <main class="app-content">
      <router-view/>
    </main>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { kpiAPI } from './services/api';

export default {
  name: 'App',
  data() {
    return {
      showNotifications: false,
      notifications: [],
      unreadCount: 0,
      pollInterval: null,
    };
  },
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
  watch: {
    isAuthenticated(val) {
      if (val) {
        this.startPolling();
      } else {
        this.stopPolling();
        this.notifications = [];
        this.unreadCount = 0;
      }
    }
  },
  mounted() {
    if (this.isAuthenticated) {
      this.startPolling();
    }
    document.addEventListener('click', this.handleOutsideClick);
  },
  beforeUnmount() {
    this.stopPolling();
    document.removeEventListener('click', this.handleOutsideClick);
  },
  methods: {
    ...mapActions(['logout']),
    handleLogout() {
      this.logout();
    },
    async fetchNotifications() {
      try {
        const [listRes, countRes] = await Promise.all([
          kpiAPI.getNotifications(),
          kpiAPI.getUnreadCount(),
        ]);
        this.notifications = listRes.data.slice(0, 20);
        this.unreadCount = countRes.data.count;
      } catch (e) {
        // Игнорируем ошибки поллинга
      }
    },
    startPolling() {
      this.fetchNotifications();
      this.pollInterval = setInterval(this.fetchNotifications, 30000);
    },
    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }
    },
    toggleNotifications() {
      this.showNotifications = !this.showNotifications;
    },
    handleOutsideClick(e) {
      if (this.$refs.bellRef && !this.$refs.bellRef.contains(e.target)) {
        this.showNotifications = false;
      }
    },
    async handleMarkRead(notif) {
      if (!notif.is_read) {
        await kpiAPI.markNotificationRead(notif.id);
        notif.is_read = true;
        this.unreadCount = Math.max(0, this.unreadCount - 1);
      }
    },
    async handleMarkAllRead() {
      await kpiAPI.markAllRead();
      this.notifications.forEach(n => { n.is_read = true; });
      this.unreadCount = 0;
    },
    notifIcon(type) {
      if (type === 'submitted') return 'П';
      if (type === 'approved') return 'ОК';
      if (type === 'rejected') return '!';
      return '·';
    },
    formatTime(dateStr) {
      const date = new Date(dateStr);
      return date.toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    },
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

/* Уведомления */
.notification-bell {
  position: relative;
}
.bell-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 8px;
  position: relative;
  font-size: 1.3rem;
  line-height: 1;
  border-radius: 50%;
  transition: background 0.2s;
}
.bell-button:hover {
  background: #f0f0f0;
}
.bell-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #dc3545;
  color: white;
  border-radius: 10px;
  font-size: 0.65rem;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
}
.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  z-index: 1000;
  overflow: hidden;
}
.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  font-weight: 600;
  font-size: 0.9rem;
}
.read-all-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0;
}
.read-all-btn:hover { text-decoration: underline; }
.notification-list {
  max-height: 400px;
  overflow-y: auto;
}
.notification-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background 0.15s;
}
.notification-item:hover { background: #f8f9fa; }
.notification-item.unread { background: #f0f7ff; }
.notification-item.unread:hover { background: #e6f2ff; }
.notif-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
  margin-top: 2px;
}
.notif-body { flex: 1; min-width: 0; }
.notif-title {
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: 3px;
}
.notif-message {
  font-size: 0.8rem;
  color: #555;
  white-space: normal;
  word-break: break-word;
}
.notif-time {
  font-size: 0.72rem;
  color: #aaa;
  margin-top: 4px;
}
.notification-empty {
  padding: 24px;
  text-align: center;
  color: #aaa;
  font-size: 0.85rem;
}

/* ===== Глобальные стили кнопок ===== */
.btn {
  padding: 9px 18px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-decoration: none;
  line-height: 1.4;
}
.btn:hover { filter: brightness(0.93); }
.btn:disabled { opacity: 0.55; cursor: not-allowed; filter: none; }

.btn-sm { padding: 5px 12px; font-size: 0.82rem; }

.btn-primary { background: #007bff; color: white; }
.btn-primary:hover { background: #0069d9; }

.btn-secondary { background: #6c757d; color: white; }
.btn-secondary:hover { background: #5a6268; }

.btn-danger { background: #dc2626; color: white; }
.btn-danger:hover { background: #b91c1c; }

.btn-outline { background: transparent; border: 1.5px solid #d1d5db; color: #374151; }
.btn-outline:hover { background: #f8f9fa; }

.btn-outline-primary { background: white; color: #007bff; border: 1.5px solid #007bff; }
.btn-outline-primary:hover { background: #f0f7ff; }

.btn-outline-excel { background: white; color: #1d6f42; border: 1.5px solid #1d6f42; }
.btn-outline-excel:hover { background: #f0fff4; }

.btn-cancel { background: white; border: 1.5px solid #d1d5db; color: #374151; }
.btn-cancel:hover { background: #f3f4f6; }

.btn-approve { background: #16a34a; color: white; }
.btn-approve:hover { background: #15803d; }

.btn-reject { background: #dc2626; color: white; }
.btn-reject:hover { background: #b91c1c; }

.btn-edit { background: #fff3cd; color: #856404; border: 1px solid #ffc107; }
.btn-edit:hover { background: #ffe8a0; }

.btn-submit { background: #d4edda; color: #155724; border: 1px solid #28a745; }
.btn-submit:hover { background: #b8dfc4; }

.btn-outline-cancel { background: transparent; border: 1.5px solid #9ca3af; color: #6b7280; }
.btn-outline-cancel:hover { background: #f3f4f6; }

/* Статус-бейджи (используются повсюду) */
.status-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; white-space: nowrap; }
.status-draft { background: #e9ecef; color: #495057; }
.status-submitted { background: #fff3cd; color: #856404; }
.status-approved { background: #d4edda; color: #155724; }
.status-rejected { background: #f8d7da; color: #721c24; }
</style>