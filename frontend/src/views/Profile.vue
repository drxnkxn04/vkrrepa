<template>
    <div class="profile-container">
      <div class="page-header">
        <h1> Профиль пользователя</h1>
      </div>
  
      <div class="profile-content">
        <!-- Карточка профиля -->
        <div class="profile-card">
          <div class="profile-avatar-section">
            <div class="profile-avatar">
              {{ userInitials }}
            </div>
            <button class="btn-change-avatar">Изменить</button>
          </div>
  
          <div class="profile-info">
            <h2>{{ currentUser?.full_name || currentUser?.username }}</h2>
            <p class="user-role">{{ profileForm.role === 'rop' ? 'РОП (руководитель)' : 'ППС (преподаватель)' }}</p>
            <p class="user-email">{{ currentUser?.email }}</p>
          </div>
        </div>
  
        <!-- Форма редактирования -->
        <div class="profile-form-card">
          <h3>Личная информация</h3>
          <form @submit.prevent="saveProfile">
            <div class="form-group">
              <label for="username">Имя пользователя</label>
              <input 
                type="text" 
                id="username" 
                v-model="profileForm.username" 
                disabled
                class="input-disabled"
              />
              <small>Имя пользователя нельзя изменить</small>
            </div>
  
            <div class="form-row">
              <div class="form-group">
                <label for="first_name">Имя</label>
                <input 
                  type="text" 
                  id="first_name" 
                  v-model="profileForm.first_name"
                />
              </div>
  
              <div class="form-group">
                <label for="last_name">Фамилия</label>
                <input 
                  type="text" 
                  id="last_name" 
                  v-model="profileForm.last_name"
                />
              </div>
            </div>
  
            <div class="form-group">
              <label for="email">Email</label>
              <input 
                type="email" 
                id="email" 
                v-model="profileForm.email"
              />
            </div>
  
            <div class="form-group">
              <label for="orcid">ORCID</label>
              <input 
                type="text" 
                id="orcid" 
                v-model="profileForm.orcid"
                placeholder="0000-0000-0000-0000"
              />
              <small>Идентификатор для автоматического импорта публикаций</small>
            </div>
  
            <div class="form-group">
              <label for="role">Роль в системе KPI</label>
              <select id="role" v-model="profileForm.role" class="form-select">
                <option value="pps">ППС (преподаватель)</option>
                <option value="rop">РОП (руководитель)</option>
              </select>
              <small>Определяет набор показателей KPI: ППС — 500 б., РОП — 700 б.</small>
            </div>

            <div class="form-group">
              <label for="department">Подразделение</label>
              <input
                type="text"
                id="department"
                v-model="profileForm.department"
                placeholder="Название подразделения"
              />
            </div>
  
            <div class="form-group">
              <label for="position">Должность</label>
              <input 
                type="text" 
                id="position" 
                v-model="profileForm.position"
                placeholder="Ваша должность"
              />
            </div>
  
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">
                 Сохранить изменения
              </button>
              <button type="button" @click="resetForm" class="btn btn-outline">
                ↻ Отменить
              </button>
            </div>
          </form>
        </div>
  
        <!-- Смена пароля -->
        <div class="password-card">
          <h3>Изменить пароль</h3>
          <form @submit.prevent="changePassword">
            <div class="form-group">
              <label for="current_password">Текущий пароль</label>
              <input 
                type="password" 
                id="current_password" 
                v-model="passwordForm.current_password"
                required
              />
            </div>
  
            <div class="form-group">
              <label for="new_password">Новый пароль</label>
              <input 
                type="password" 
                id="new_password" 
                v-model="passwordForm.new_password"
                required
              />
              <small>Минимум 8 символов</small>
            </div>
  
            <div class="form-group">
              <label for="confirm_password">Подтвердите пароль</label>
              <input 
                type="password" 
                id="confirm_password" 
                v-model="passwordForm.confirm_password"
                required
              />
            </div>
  
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">
                 Изменить пароль
              </button>
            </div>
          </form>
        </div>
  
        <!-- Синхронизация Crossref -->
        <div class="sync-card">
          <h3> Синхронизация публикаций</h3>
          <p>Автоматически импортировать ваши публикации из Crossref по ORCID</p>
          
          <div v-if="profileForm.orcid" class="sync-content">
            <div class="sync-info">
              <p><strong>ORCID:</strong> {{ profileForm.orcid }}</p>
              <p v-if="lastSyncDate"><strong>Последняя синхронизация:</strong> {{ lastSyncDate }}</p>
            </div>
            
            <button 
              @click="syncPublications" 
              class="btn btn-secondary"
              :disabled="syncing"
            >
              {{ syncing ? '⏳ Синхронизация...' : ' Синхронизировать' }}
            </button>
          </div>
  
          <div v-else class="sync-warning">
            ⚠️ Укажите ORCID в профиле для активации автоматической синхронизации
          </div>
        </div>
  
        <!-- Статистика пользователя -->
        <div class="stats-card">
          <h3> Ваша статистика</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-icon"></div>
              <div class="stat-content">
                <p class="stat-value">—</p>
                <p class="stat-label">Всего записей KPI</p>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon">⭐</div>
              <div class="stat-content">
                <p class="stat-value">—</p>
                <p class="stat-label">Средний балл</p>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon"></div>
              <div class="stat-content">
                <p class="stat-value">—</p>
                <p class="stat-label">Лучший результат</p>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon"></div>
              <div class="stat-content">
                <p class="stat-value">—</p>
                <p class="stat-label">Активных месяцев</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { mapGetters } from 'vuex';
  import { kpiAPI } from '@/services/api';
  
  export default {
    name: 'ProfileView',
    data() {
      return {
        profileForm: {
          username: '',
          first_name: '',
          last_name: '',
          email: '',
          orcid: '',
          role: 'pps',
          department: '',
          position: ''
        },
        passwordForm: {
          current_password: '',
          new_password: '',
          confirm_password: ''
        },
        syncing: false,
        lastSyncDate: null
      };
    },
    computed: {
      ...mapGetters(['currentUser']),
      userInitials() {
        const name = this.currentUser?.full_name || this.currentUser?.username || 'User';
        return name
          .split(' ')
          .map(word => word[0])
          .join('')
          .toUpperCase()
          .slice(0, 2);
      }
    },
    created() {
      this.loadProfile();
    },
    methods: {
      async loadProfile() {
        try {
          const response = await kpiAPI.getProfile();
          const data = response.data;
          this.profileForm.username = data.username || '';
          this.profileForm.first_name = data.first_name || '';
          this.profileForm.last_name = data.last_name || '';
          this.profileForm.email = data.email || '';
          this.profileForm.orcid = data.orcid || '';
          this.profileForm.role = data.role || 'pps';
          this.profileForm.department = data.department || '';
          this.profileForm.position = data.position || '';
        } catch (error) {
          console.error('Ошибка загрузки профиля:', error);
        }
      },
      async saveProfile() {
        // Валидация ORCID на клиенте
        if (this.profileForm.orcid) {
          const orcidPattern = /^\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$/;
          if (!orcidPattern.test(this.profileForm.orcid)) {
            this.$toast.error('Неверный формат ORCID. Ожидается: 0000-0000-0000-0000');
            return;
          }
        }

        try {
          await kpiAPI.updateProfile({
            first_name: this.profileForm.first_name,
            last_name: this.profileForm.last_name,
            email: this.profileForm.email,
            orcid: this.profileForm.orcid,
            role: this.profileForm.role,
            department: this.profileForm.department,
            position: this.profileForm.position,
          });
          this.$toast.success('Профиль обновлен');
        } catch (error) {
          const msg = error.response?.data?.error || 'Не удалось сохранить профиль';
          this.$toast.error(msg);
        }
      },
      resetForm() {
        this.loadProfile();
        this.$toast.info('Изменения отменены');
      },
      async changePassword() {
        // Проверка совпадения паролей
        if (this.passwordForm.new_password !== this.passwordForm.confirm_password) {
          this.$toast.error('Пароли не совпадают');
          return;
        }
  
        // Проверка длины пароля
        if (this.passwordForm.new_password.length < 8) {
          this.$toast.error('Пароль должен быть не менее 8 символов');
          return;
        }
  
        try {
          // Здесь должен быть API запрос на смену пароля
          // await api.changePassword(this.passwordForm);
          
          this.$toast.success('Пароль изменен');
          
          // Очистка формы
          this.passwordForm = {
            current_password: '',
            new_password: '',
            confirm_password: ''
          };
        } catch (error) {
          console.error('Ошибка смены пароля:', error);
          this.$toast.error('Не удалось изменить пароль');
        }
      },
      async syncPublications() {
        if (!this.profileForm.orcid) {
          this.$toast.error('Укажите ORCID в профиле');
          return;
        }
  
        this.syncing = true;
        try {
          const response = await kpiAPI.syncCrossref({
            orcid: this.profileForm.orcid,
            year: new Date().getFullYear()
          });
  
          if (response.data.success) {
            this.$toast.success(
              `Синхронизировано публикаций: ${response.data.publications_count}`
            );
            this.lastSyncDate = new Date().toLocaleDateString('ru-RU');
          }
        } catch (error) {
          console.error('Ошибка синхронизации:', error);
          this.$toast.error('Не удалось синхронизировать публикации');
        } finally {
          this.syncing = false;
        }
      }
    }
  };
  </script>
  
  <style scoped>
  .profile-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .page-header {
    margin-bottom: 32px;
  }
  
  .page-header h1 {
    margin: 0;
    color: #2c3e50;
  }
  
  .profile-content {
    display: grid;
    gap: 24px;
  }
  
  /* Profile Card */
  .profile-card {
    background: white;
    border-radius: 8px;
    padding: 32px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 32px;
  }
  
  .profile-avatar-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }
  
  .profile-avatar {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    font-weight: bold;
  }
  
  .btn-change-avatar {
    padding: 6px 16px;
    border: 1px solid #ddd;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
  }
  
  .btn-change-avatar:hover {
    background: #f8f9fa;
  }
  
  .profile-info {
    flex: 1;
  }
  
  .profile-info h2 {
    margin: 0 0 8px 0;
    color: #2c3e50;
  }
  
  .user-role {
    margin: 0 0 4px 0;
    color: #7f8c8d;
    font-weight: 500;
  }
  
  .user-email {
    margin: 0;
    color: #95a5a6;
  }
  
  /* Form Cards */
  .profile-form-card,
  .password-card,
  .sync-card,
  .stats-card {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .profile-form-card h3,
  .password-card h3,
  .sync-card h3,
  .stats-card h3 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #2c3e50;
  }
  
  /* Forms */
  .form-group {
    margin-bottom: 20px;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #2c3e50;
  }
  
  .form-group input,
  .form-group .form-select {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    box-sizing: border-box;
    transition: border-color 0.2s;
    background: white;
  }
  
  .form-group input:focus {
    outline: none;
    border-color: #3498db;
  }
  
  .form-group input.input-disabled {
    background: #f8f9fa;
    cursor: not-allowed;
  }
  
  .form-group small {
    display: block;
    margin-top: 4px;
    font-size: 0.85rem;
    color: #7f8c8d;
  }
  
  .form-actions {
    display: flex;
    gap: 12px;
    margin-top: 24px;
  }
  
  /* Sync Card */
  .sync-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
    margin-top: 16px;
  }
  
  .sync-info {
    flex: 1;
  }
  
  .sync-info p {
    margin: 4px 0;
    color: #2c3e50;
  }
  
  .sync-warning {
    padding: 16px;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 6px;
    color: #856404;
    margin-top: 16px;
  }
  
  /* Stats Grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-top: 16px;
  }
  
  .stat-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
  }
  
  .stat-icon {
    font-size: 2rem;
  }
  
  .stat-content {
    flex: 1;
  }
  
  .stat-value {
    margin: 0 0 4px 0;
    font-size: 1.5rem;
    font-weight: bold;
    color: #2c3e50;
  }
  
  .stat-label {
    margin: 0;
    font-size: 0.85rem;
    color: #7f8c8d;
  }
  
  /* Buttons */
  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
    font-size: 14px;
  }
  
  .btn:hover:not(:disabled) {
    opacity: 0.9;
    transform: translateY(-1px);
  }
  
  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .btn-primary {
    background: #3498db;
    color: white;
  }
  
  .btn-secondary {
    background: #95a5a6;
    color: white;
  }
  
  .btn-outline {
    background: transparent;
    border: 1px solid #95a5a6;
    color: #95a5a6;
  }
  
  .btn-outline:hover {
    background: #f8f9fa;
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .profile-card {
      flex-direction: column;
      text-align: center;
    }
  
    .form-row {
      grid-template-columns: 1fr;
    }
  
    .sync-content {
      flex-direction: column;
      gap: 16px;
    }
  
    .form-actions {
      flex-direction: column;
    }
  
    .form-actions .btn {
      width: 100%;
    }
  }
  </style>