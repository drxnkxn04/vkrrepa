<template>
    <div class="notfound-container">
      <div class="notfound-content">
        <div class="notfound-animation">
          <div class="notfound-icon">🔍</div>
          <div class="notfound-404">404</div>
        </div>
  
        <h1>Страница не найдена</h1>
        <p class="notfound-message">
          К сожалению, запрашиваемая страница не существует или была перемещена.
        </p>
  
        <div class="notfound-suggestions">
          <h3>Возможно, вы искали:</h3>
          <ul>
            <li>
              <router-link to="/">
                🏠 Главная страница (Дашборд)
              </router-link>
            </li>
            <li>
              <router-link to="/history">
                📊 История KPI
              </router-link>
            </li>
            <li>
              <router-link to="/recommendations">
                💡 Рекомендации
              </router-link>
            </li>
            <li>
              <router-link to="/profile">
                👤 Профиль
              </router-link>
            </li>
            <li v-if="isAdmin">
              <router-link to="/manager">
                👔 Дашборд руководителя
              </router-link>
            </li>
          </ul>
        </div>
  
        <div class="notfound-actions">
          <button @click="goBack" class="btn btn-outline">
            ← Вернуться назад
          </button>
          <router-link to="/" class="btn btn-primary">
            🏠 На главную
          </router-link>
        </div>
  
        <div class="notfound-help">
          <p>
            Если вы считаете, что это ошибка, пожалуйста, 
            <a href="mailto:support@example.com">свяжитесь с поддержкой</a>.
          </p>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { mapGetters } from 'vuex';
  
  export default {
    name: 'NotFoundView',
    computed: {
      ...mapGetters(['isAdmin'])
    },
    methods: {
      goBack() {
        // Проверяем, есть ли история
        if (window.history.length > 2) {
          this.$router.go(-1);
        } else {
          this.$router.push('/');
        }
      }
    }
  };
  </script>
  
  <style scoped>
  .notfound-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  .notfound-content {
    max-width: 600px;
    text-align: center;
    background: white;
    border-radius: 16px;
    padding: 48px 32px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  }
  
  /* Animation */
  .notfound-animation {
    position: relative;
    margin-bottom: 32px;
  }
  
  .notfound-icon {
    font-size: 4rem;
    animation: float 3s ease-in-out infinite;
  }
  
  @keyframes float {
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-20px);
    }
  }
  
  .notfound-404 {
    font-size: 8rem;
    font-weight: bold;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    margin: 16px 0;
    animation: pulse 2s ease-in-out infinite;
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }
  
  /* Content */
  .notfound-content h1 {
    margin: 0 0 16px 0;
    color: #2c3e50;
    font-size: 2rem;
  }
  
  .notfound-message {
    color: #7f8c8d;
    font-size: 1.1rem;
    line-height: 1.6;
    margin-bottom: 32px;
  }
  
  /* Suggestions */
  .notfound-suggestions {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 32px;
    text-align: left;
  }
  
  .notfound-suggestions h3 {
    margin-top: 0;
    margin-bottom: 16px;
    color: #2c3e50;
    font-size: 1.1rem;
  }
  
  .notfound-suggestions ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .notfound-suggestions li {
    margin-bottom: 12px;
  }
  
  .notfound-suggestions a {
    color: #3498db;
    text-decoration: none;
    font-weight: 500;
    display: flex;
    align-items: center;
    transition: all 0.2s;
    padding: 8px;
    border-radius: 4px;
  }
  
  .notfound-suggestions a:hover {
    background: white;
    transform: translateX(4px);
  }
  
  /* Actions */
  .notfound-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }
  
  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s;
    text-decoration: none;
    display: inline-block;
  }
  
  .btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .btn-outline {
    background: transparent;
    border: 2px solid #3498db;
    color: #3498db;
  }
  
  .btn-outline:hover {
    background: #3498db;
    color: white;
  }
  
  /* Help */
  .notfound-help {
    padding-top: 24px;
    border-top: 1px solid #e9ecef;
  }
  
  .notfound-help p {
    margin: 0;
    color: #95a5a6;
    font-size: 0.9rem;
  }
  
  .notfound-help a {
    color: #3498db;
    text-decoration: none;
    font-weight: 500;
  }
  
  .notfound-help a:hover {
    text-decoration: underline;
  }
  
  /* Responsive */
  @media (max-width: 600px) {
    .notfound-content {
      padding: 32px 20px;
    }
  
    .notfound-404 {
      font-size: 5rem;
    }
  
    .notfound-content h1 {
      font-size: 1.5rem;
    }
  
    .notfound-actions {
      flex-direction: column;
    }
  
    .btn {
      width: 100%;
    }
  }
  </style>