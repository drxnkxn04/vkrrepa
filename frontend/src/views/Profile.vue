<template>
  <div class="profile-container">
    <div class="page-header">
      <h1>Профиль</h1>
    </div>

    <div class="profile-content">
      <!-- Карточка профиля -->
      <div class="profile-card">
        <div class="avatar-section">
          <div class="avatar-wrapper" @click="$refs.avatarInput.click()">
            <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" alt="Аватар" />
            <div v-else class="avatar-placeholder">{{ userInitials }}</div>
            <div class="avatar-overlay">
              <span>Изменить</span>
            </div>
          </div>
          <input
            ref="avatarInput"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            class="hidden-input"
            @change="handleAvatarChange"
          />
          <button v-if="avatarUrl" @click="removeAvatar" class="btn-remove-avatar">
            Удалить фото
          </button>
        </div>
        <div class="profile-info">
          <h2>{{ currentUser?.full_name || currentUser?.username }}</h2>
          <span class="role-badge" :class="profileData.role">
            {{ profileData.role === 'rop' ? 'РОП (руководитель)' : 'ППС (преподаватель)' }}
          </span>
          <p class="user-meta" v-if="profileData.department || profileData.position">
            <span v-if="profileData.position">{{ profileData.position }}</span>
            <span v-if="profileData.position && profileData.department"> · </span>
            <span v-if="profileData.department">{{ profileData.department }}</span>
          </p>
        </div>
      </div>

      <!-- Личная информация -->
      <div class="form-card">
        <h3>Личная информация</h3>
        <form @submit.prevent="saveProfile">
          <div class="form-group">
            <label>Имя пользователя</label>
            <input type="text" :value="profileData.username" disabled class="input-disabled" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="first_name">Имя</label>
              <input type="text" id="first_name" v-model="profileForm.first_name" />
            </div>
            <div class="form-group">
              <label for="last_name">Фамилия</label>
              <input type="text" id="last_name" v-model="profileForm.last_name" />
            </div>
          </div>

          <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" v-model="profileForm.email" />
          </div>

          <div class="form-group">
            <label for="orcid">ORCID</label>
            <input
              type="text"
              id="orcid"
              v-model="profileForm.orcid"
              placeholder="0000-0000-0000-0000"
            />
            <small>Ваш идентификатор ORCID</small>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
            <button type="button" @click="resetForm" class="btn btn-outline">
              Отменить
            </button>
          </div>
        </form>
      </div>

      <!-- Смена пароля -->
      <div class="form-card">
        <h3>Смена пароля</h3>
        <form @submit.prevent="changePassword">
          <div class="form-group">
            <label for="current_password">Текущий пароль</label>
            <input type="password" id="current_password" v-model="passwordForm.current_password" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="new_password">Новый пароль</label>
              <input type="password" id="new_password" v-model="passwordForm.new_password" required />
            </div>
            <div class="form-group">
              <label for="confirm_password">Подтверждение</label>
              <input type="password" id="confirm_password" v-model="passwordForm.confirm_password" required />
            </div>
          </div>
          <small class="password-hint">Минимум 8 символов</small>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="changingPassword">
              {{ changingPassword ? 'Сохранение...' : 'Изменить пароль' }}
            </button>
          </div>
        </form>
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
      profileData: {
        username: '',
        role: 'pps',
        department: '',
        position: '',
      },
      profileForm: {
        first_name: '',
        last_name: '',
        email: '',
        orcid: '',
      },
      avatarUrl: null,
      passwordForm: {
        current_password: '',
        new_password: '',
        confirm_password: '',
      },
      saving: false,
      changingPassword: false,
    };
  },
  computed: {
    ...mapGetters(['currentUser']),
    userInitials() {
      const name = this.currentUser?.full_name || this.currentUser?.username || 'U';
      return name
        .split(' ')
        .map(word => word[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    },
  },
  created() {
    this.loadProfile();
  },
  methods: {
    async loadProfile() {
      try {
        const response = await kpiAPI.getProfile();
        const data = response.data;
        this.profileData.username = data.username || '';
        this.profileData.role = data.role || 'pps';
        this.profileData.department = data.department || '';
        this.profileData.position = data.position || '';
        this.profileForm.first_name = data.first_name || '';
        this.profileForm.last_name = data.last_name || '';
        this.profileForm.email = data.email || '';
        this.profileForm.orcid = data.orcid || '';
        this.avatarUrl = data.avatar || null;
      } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
        this.$toast.error('Не удалось загрузить профиль');
      }
    },

    async saveProfile() {
      if (this.profileForm.orcid) {
        const orcidPattern = /^\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$/;
        if (!orcidPattern.test(this.profileForm.orcid)) {
          this.$toast.error('Неверный формат ORCID. Ожидается: 0000-0000-0000-0000');
          return;
        }
      }

      this.saving = true;
      try {
        await kpiAPI.updateProfile({
          first_name: this.profileForm.first_name,
          last_name: this.profileForm.last_name,
          email: this.profileForm.email,
          orcid: this.profileForm.orcid,
        });
        this.$toast.success('Профиль обновлён');
      } catch (error) {
        const msg = error.response?.data?.error || 'Не удалось сохранить профиль';
        this.$toast.error(msg);
      } finally {
        this.saving = false;
      }
    },

    resetForm() {
      this.loadProfile();
      this.$toast.info('Изменения отменены');
    },

    async handleAvatarChange(event) {
      const file = event.target.files[0];
      if (!file) return;

      // Сбрасываем input, чтобы можно было выбрать тот же файл повторно
      event.target.value = '';

      try {
        const response = await kpiAPI.uploadAvatar(file);
        this.avatarUrl = response.data.avatar;
        this.$toast.success('Аватар обновлён');
      } catch (error) {
        const msg = error.response?.data?.error || 'Не удалось загрузить аватар';
        this.$toast.error(msg);
      }
    },

    async removeAvatar() {
      try {
        await kpiAPI.deleteAvatar();
        this.avatarUrl = null;
        this.$toast.success('Аватар удалён');
      } catch {
        this.$toast.error('Не удалось удалить аватар');
      }
    },

    async changePassword() {
      if (this.passwordForm.new_password !== this.passwordForm.confirm_password) {
        this.$toast.error('Пароли не совпадают');
        return;
      }

      if (this.passwordForm.new_password.length < 8) {
        this.$toast.error('Пароль должен быть не менее 8 символов');
        return;
      }

      this.changingPassword = true;
      try {
        await kpiAPI.changePassword({
          current_password: this.passwordForm.current_password,
          new_password: this.passwordForm.new_password,
        });
        this.$toast.success('Пароль изменён');
        this.passwordForm = { current_password: '', new_password: '', confirm_password: '' };
      } catch (error) {
        const msg = error.response?.data?.error || 'Не удалось изменить пароль';
        this.$toast.error(msg);
      } finally {
        this.changingPassword = false;
      }
    },
  },
};
</script>

<style scoped>
.profile-container {
  max-width: 700px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 28px;
}

.page-header h1 {
  margin: 0;
  color: #1a202c;
  font-size: 1.5rem;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Profile card */
.profile-card {
  background: white;
  border-radius: 10px;
  padding: 28px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 24px;
}

/* Avatar */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.avatar-wrapper {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  position: relative;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.2rem;
  font-weight: 700;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 600;
  opacity: 0;
  transition: opacity 0.2s;
  border-radius: 50%;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.btn-remove-avatar {
  background: none;
  border: none;
  color: #dc2626;
  font-size: 0.78rem;
  cursor: pointer;
  padding: 0;
}

.btn-remove-avatar:hover {
  text-decoration: underline;
}

.hidden-input {
  display: none;
}

.profile-info h2 {
  margin: 0 0 6px;
  font-size: 1.25rem;
  color: #1a202c;
}

.role-badge {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 600;
}

.role-badge.pps {
  background: #dbeafe;
  color: #1e40af;
}

.role-badge.rop {
  background: #ede9fe;
  color: #6d28d9;
}

.user-meta {
  margin: 6px 0 0;
  font-size: 0.88rem;
  color: #6b7280;
}

/* Form card */
.form-card {
  background: white;
  border-radius: 10px;
  padding: 28px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.form-card h3 {
  margin: 0 0 20px;
  font-size: 1.1rem;
  color: #1a202c;
}

.form-group {
  margin-bottom: 18px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  color: #374151;
}

.form-group input {
  width: 100%;
  padding: 9px 12px;
  border: 1.5px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.92rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
  font-family: inherit;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input.input-disabled {
  background: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.form-group small,
.password-hint {
  display: block;
  margin-top: 4px;
  font-size: 0.82rem;
  color: #9ca3af;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 24px;
}

/* Кнопки — глобальные стили в App.vue */
.btn-primary { background: #667eea; }

@media (max-width: 640px) {
  .profile-card {
    flex-direction: column;
    text-align: center;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .form-actions .btn {
    width: 100%;
  }
}
</style>
