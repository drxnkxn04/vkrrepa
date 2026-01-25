<!-- frontend/src/views/Login.vue -->
<template>
  <div class="login-container">
    <div class="login-box">
      <h2>Вход в систему KPI</h2>
      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <label for="username">Имя пользователя</label>
          <input type="text" id="username" v-model="username" required>
        </div>
        <div class="input-group">
          <label for="password">Пароль</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <button type="submit" :disabled="authStatus === 'loading'">
          {{ authStatus === 'loading' ? 'Вход...' : 'Войти' }}
        </button>
        <p v-if="error" class="error-message">
          {{ error }}
        </p>
      </form>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

export default {
  name: 'LoginView',
  data() {
    return {
      username: '',
      password: '',
      error: null
    };
  },
  computed: {
    ...mapGetters(['authStatus', 'error']),
  },
  methods: {
    ...mapActions(['login']),
    async handleLogin() {
      this.error = null;
      try {
        await this.login({
          username: this.username,
          password: this.password,
        });
      } catch (error) {
        this.$toast.error('Неверное имя пользователя или пароль');
      }
    },
  },
};
</script>

<style scoped>
.login-container { 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  height: 100vh; 
  background-color: #f4f7f6; 
}
.login-box { 
  padding: 40px; 
  background: white; 
  border-radius: 8px; 
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); 
  width: 100%; 
  max-width: 400px; 
}
h2 { 
  text-align: center; 
  margin-bottom: 20px; 
  color: #333; 
}
.input-group { margin-bottom: 15px; }
label { 
  display: block; 
  margin-bottom: 5px; 
  color: #555; 
}
input { 
  width: 100%; 
  padding: 10px; 
  border: 1px solid #ccc; 
  border-radius: 4px; 
  box-sizing: border-box; 
}
button { 
  width: 100%; 
  padding: 10px; 
  background-color: #007bff; 
  color: white; 
  border: none; 
  border-radius: 4px; 
  cursor: pointer; 
  font-size: 16px;
  transition: opacity 0.2s;
}
button:hover {
  opacity: 0.9;
}
button:disabled { 
  background-color: #aaa; 
  cursor: not-allowed;
}
.error-message { 
  color: #d93025; 
  text-align: center; 
  margin-top: 10px; 
}
</style>