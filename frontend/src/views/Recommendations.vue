<template>
    <div class="recommendations-container">
      <div class="page-header">
        <h1>💡 Рекомендации по улучшению</h1>
        <div class="header-actions">
          <button @click="refreshRecommendations" class="btn btn-secondary">
            🔄 Обновить
          </button>
        </div>
      </div>
  
      <!-- Загрузка -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка рекомендаций...</p>
      </div>
  
      <!-- Основной контент -->
      <div v-else-if="recommendations.length > 0">
        <!-- Сводка -->
        <div class="summary-section">
          <div class="summary-card priority-high">
            <div class="summary-icon">🔴</div>
            <div class="summary-content">
              <h3>Высокий приоритет</h3>
              <p class="summary-value">{{ highPriorityCount }}</p>
            </div>
          </div>
          
          <div class="summary-card priority-medium">
            <div class="summary-icon">🟡</div>
            <div class="summary-content">
              <h3>Средний приоритет</h3>
              <p class="summary-value">{{ mediumPriorityCount }}</p>
            </div>
          </div>
          
          <div class="summary-card priority-low">
            <div class="summary-icon">🟢</div>
            <div class="summary-content">
              <h3>Низкий приоритет</h3>
              <p class="summary-value">{{ lowPriorityCount }}</p>
            </div>
          </div>
        </div>
  
        <!-- Фильтры -->
        <div class="filters-section">
          <div class="filter-buttons">
            <button 
              :class="['filter-btn', { active: selectedFilter === 'all' }]"
              @click="setFilter('all')"
            >
              Все ({{ recommendations.length }})
            </button>
            <button 
              :class="['filter-btn', { active: selectedFilter === 'active' }]"
              @click="setFilter('active')"
            >
              Активные ({{ activeCount }})
            </button>
            <button 
              :class="['filter-btn', { active: selectedFilter === 'completed' }]"
              @click="setFilter('completed')"
            >
              Выполненные ({{ completedCount }})
            </button>
          </div>
        </div>
  
        <!-- Список рекомендаций -->
        <div class="recommendations-grid">
          <div 
            v-for="rec in filteredRecommendations" 
            :key="rec.id" 
            class="recommendation-card"
            :class="{ completed: rec.is_completed }"
          >
            <!-- Заголовок -->
            <div class="rec-header">
              <div class="rec-title-section">
                <span class="rec-priority" :class="'priority-' + getPriority(rec)">
                  {{ getPriorityIcon(rec) }}
                </span>
                <h3>{{ rec.indicator_name }}</h3>
              </div>
              <span v-if="rec.is_completed" class="completed-badge">✓ Выполнено</span>
            </div>
  
            <!-- Прогресс -->
            <div class="rec-progress">
              <div class="progress-info">
                <span class="progress-label">Текущее выполнение:</span>
                <span class="progress-value" :class="getProgressClass(rec.current_completion)">
                  {{ rec.current_completion.toFixed(1) }}%
                </span>
              </div>
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: rec.current_completion + '%' }"
                  :class="getProgressClass(rec.current_completion)"
                ></div>
              </div>
            </div>
  
            <!-- Текст рекомендации -->
            <div class="rec-body">
              <p>{{ rec.text }}</p>
            </div>
  
            <!-- Метаданные -->
            <div class="rec-metadata">
              <div class="metadata-item">
                <span class="metadata-label">🎯 Целевое значение:</span>
                <span class="metadata-value">{{ rec.target_value.toFixed(1) }}</span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">📅 Срок выполнения:</span>
                <span class="metadata-value">{{ formatPeriod(rec.deadline_period) }}</span>
              </div>
              <div class="metadata-item">
                <span class="metadata-label">📊 Необходимо улучшить:</span>
                <span class="metadata-value improvement">
                  +{{ (rec.target_value - rec.current_completion).toFixed(1) }}%
                </span>
              </div>
            </div>
  
            <!-- Действия -->
            <div class="rec-actions">
              <button 
                v-if="!rec.is_completed"
                @click="markAsCompleted(rec.id)" 
                class="btn btn-success"
              >
                ✓ Отметить выполненным
              </button>
              <button 
                v-else
                @click="markAsActive(rec.id)" 
                class="btn btn-outline"
              >
                ↻ Вернуть в активные
              </button>
              <button @click="viewDetails(rec)" class="btn btn-outline">
                👁️ Подробнее
              </button>
            </div>
          </div>
        </div>
      </div>
  
      <!-- Пустое состояние -->
      <div v-else class="empty-state">
        <div class="empty-icon">🎉</div>
        <h2>Отлично! У вас нет активных рекомендаций</h2>
        <p>Все показатели выполняются на достаточном уровне</p>
        <router-link to="/" class="btn btn-primary">
          Перейти к дашборду
        </router-link>
      </div>
  
      <!-- Модальное окно с деталями (опционально) -->
      <div v-if="showDetailModal" class="modal-backdrop" @click.self="closeDetailModal">
        <div class="modal-content">
          <div class="modal-header">
            <h2>{{ selectedRecommendation?.indicator_name }}</h2>
            <button @click="closeDetailModal" class="close-button">&times;</button>
          </div>
          <div class="modal-body">
            <p><strong>Рекомендация:</strong></p>
            <p>{{ selectedRecommendation?.text }}</p>
            
            <div class="modal-stats">
              <div class="modal-stat">
                <span>Текущий прогресс:</span>
                <strong>{{ selectedRecommendation?.current_completion.toFixed(1) }}%</strong>
              </div>
              <div class="modal-stat">
                <span>Целевое значение:</span>
                <strong>{{ selectedRecommendation?.target_value.toFixed(1) }}</strong>
              </div>
              <div class="modal-stat">
                <span>Срок:</span>
                <strong>{{ formatPeriod(selectedRecommendation?.deadline_period) }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { kpiAPI } from '@/services/api';
  
  export default {
    name: 'RecommendationsView',
    data() {
      return {
        recommendations: [],
        loading: false,
        selectedFilter: 'all',
        showDetailModal: false,
        selectedRecommendation: null
      };
    },
    computed: {
      filteredRecommendations() {
        if (this.selectedFilter === 'all') {
          return this.recommendations;
        }
        if (this.selectedFilter === 'active') {
          return this.recommendations.filter(r => !r.is_completed);
        }
        if (this.selectedFilter === 'completed') {
          return this.recommendations.filter(r => r.is_completed);
        }
        return this.recommendations;
      },
      activeCount() {
        return this.recommendations.filter(r => !r.is_completed).length;
      },
      completedCount() {
        return this.recommendations.filter(r => r.is_completed).length;
      },
      highPriorityCount() {
        return this.recommendations.filter(r => this.getPriority(r) === 'high').length;
      },
      mediumPriorityCount() {
        return this.recommendations.filter(r => this.getPriority(r) === 'medium').length;
      },
      lowPriorityCount() {
        return this.recommendations.filter(r => this.getPriority(r) === 'low').length;
      }
    },
    async created() {
      await this.loadRecommendations();
    },
    methods: {
      async loadRecommendations() {
        this.loading = true;
        try {
          // Загружаем рекомендации для текущего периода
          const now = new Date();
          const period = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
          
          const response = await kpiAPI.getRecommendations(period);
          this.recommendations = response.data;
        } catch (error) {
          console.error('Ошибка загрузки рекомендаций:', error);
          this.$toast.error('Не удалось загрузить рекомендации');
        } finally {
          this.loading = false;
        }
      },
      async refreshRecommendations() {
        await this.loadRecommendations();
        this.$toast.success('Рекомендации обновлены');
      },
      async markAsCompleted(recId) {
        try {
          await kpiAPI.completeRecommendation(recId);
          this.$toast.success('Рекомендация отмечена как выполненная');
          await this.loadRecommendations();
        } catch (error) {
          console.error('Ошибка отметки рекомендации:', error);
          this.$toast.error('Не удалось отметить рекомендацию');
        }
      },
      async markAsActive(recId) {
        // Заглушка для возврата рекомендации в активные
        this.$toast.info('Функция в разработке');
      },
      setFilter(filter) {
        this.selectedFilter = filter;
      },
      getPriority(rec) {
        // Определяем приоритет на основе текущего выполнения
        if (rec.current_completion < 50) return 'high';
        if (rec.current_completion < 70) return 'medium';
        return 'low';
      },
      getPriorityIcon(rec) {
        const priority = this.getPriority(rec);
        if (priority === 'high') return '🔴';
        if (priority === 'medium') return '🟡';
        return '🟢';
      },
      getProgressClass(value) {
        if (value >= 70) return 'good';
        if (value >= 50) return 'medium';
        return 'poor';
      },
      formatPeriod(period) {
        if (!period) return '—';
        const [year, month] = period.split('-');
        const monthNames = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                            'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
        return `${monthNames[parseInt(month) - 1]} ${year}`;
      },
      viewDetails(rec) {
        this.selectedRecommendation = rec;
        this.showDetailModal = true;
      },
      closeDetailModal() {
        this.showDetailModal = false;
        this.selectedRecommendation = null;
      }
    }
  };
  </script>
  
  <style scoped>
  .recommendations-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
  }
  
  .page-header h1 {
    margin: 0;
    color: #2c3e50;
  }
  
  /* Summary */
  .summary-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 32px;
  }
  
  .summary-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 16px;
    border-left: 4px solid;
  }
  
  .summary-card.priority-high {
    border-left-color: #e74c3c;
  }
  
  .summary-card.priority-medium {
    border-left-color: #f39c12;
  }
  
  .summary-card.priority-low {
    border-left-color: #27ae60;
  }
  
  .summary-icon {
    font-size: 2.5rem;
  }
  
  .summary-content h3 {
    margin: 0 0 8px 0;
    font-size: 0.9rem;
    color: #7f8c8d;
  }
  
  .summary-value {
    margin: 0;
    font-size: 1.8rem;
    font-weight: bold;
    color: #2c3e50;
  }
  
  /* Filters */
  .filters-section {
    background: white;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-bottom: 24px;
  }
  
  .filter-buttons {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  
  .filter-btn {
    padding: 10px 20px;
    border: 1px solid #ddd;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
  }
  
  .filter-btn:hover {
    background: #f8f9fa;
  }
  
  .filter-btn.active {
    background: #3498db;
    color: white;
    border-color: #3498db;
  }
  
  /* Recommendations Grid */
  .recommendations-grid {
    display: grid;
    gap: 24px;
  }
  
  .recommendation-card {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #3498db;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  
  .recommendation-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .recommendation-card.completed {
    opacity: 0.7;
    border-left-color: #95a5a6;
  }
  
  /* Header */
  .rec-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
  }
  
  .rec-title-section {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .rec-priority {
    font-size: 1.5rem;
  }
  
  .rec-header h3 {
    margin: 0;
    color: #2c3e50;
    font-size: 1.2rem;
  }
  
  .completed-badge {
    background: #27ae60;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 500;
  }
  
  /* Progress */
  .rec-progress {
    margin-bottom: 16px;
  }
  
  .progress-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  
  .progress-label {
    font-size: 0.9rem;
    color: #7f8c8d;
  }
  
  .progress-value {
    font-weight: 600;
    font-size: 1rem;
  }
  
  .progress-value.good { color: #27ae60; }
  .progress-value.medium { color: #f39c12; }
  .progress-value.poor { color: #e74c3c; }
  
  .progress-bar {
    height: 12px;
    background: #e9ecef;
    border-radius: 6px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    transition: width 0.5s ease;
    border-radius: 6px;
  }
  
  .progress-fill.good { background: #27ae60; }
  .progress-fill.medium { background: #f39c12; }
  .progress-fill.poor { background: #e74c3c; }
  
  /* Body */
  .rec-body {
    margin-bottom: 16px;
    line-height: 1.6;
    color: #2c3e50;
  }
  
  /* Metadata */
  .rec-metadata {
    display: grid;
    gap: 12px;
    margin-bottom: 16px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
  }
  
  .metadata-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .metadata-label {
    font-size: 0.9rem;
    color: #7f8c8d;
  }
  
  .metadata-value {
    font-weight: 600;
    color: #2c3e50;
  }
  
  .metadata-value.improvement {
    color: #3498db;
  }
  
  /* Actions */
  .rec-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
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
  
  .btn:hover {
    opacity: 0.9;
    transform: translateY(-1px);
  }
  
  .btn-primary {
    background: #3498db;
    color: white;
  }
  
  .btn-secondary {
    background: #95a5a6;
    color: white;
  }
  
  .btn-success {
    background: #27ae60;
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
  
  /* Modal */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .modal-content {
    background: white;
    border-radius: 8px;
    width: 90%;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
  }
  
  .modal-header {
    padding: 20px;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .modal-header h2 {
    margin: 0;
    color: #2c3e50;
  }
  
  .close-button {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #95a5a6;
  }
  
  .modal-body {
    padding: 20px;
  }
  
  .modal-stats {
    display: grid;
    gap: 12px;
    margin-top: 20px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
  }
  
  .modal-stat {
    display: flex;
    justify-content: space-between;
  }
  
  /* States */
  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    text-align: center;
  }
  
  .spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .empty-icon {
    font-size: 4rem;
    margin-bottom: 16px;
  }
  
  .empty-state h2 {
    color: #27ae60;
    margin-bottom: 8px;
  }
  
  .empty-state p {
    color: #7f8c8d;
    margin-bottom: 24px;
  }
  </style>