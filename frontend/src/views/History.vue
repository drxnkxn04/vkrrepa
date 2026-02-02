<template>
    <div class="history-container">
      <div class="page-header">
        <h1>История KPI</h1>
        <div class="controls">
          <label for="months">Период:</label>
          <select id="months" v-model="selectedMonths" @change="loadHistory">
            <option :value="3">3 месяца</option>
            <option :value="6">6 месяцев</option>
            <option :value="12">12 месяцев</option>
            <option :value="24">24 месяца</option>
          </select>
          <button @click="exportToExcel" class="btn btn-secondary">
             Экспорт в Excel
          </button>
        </div>
      </div>
  
      <!-- Загрузка -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка истории...</p>
      </div>
  
      <!-- Основной контент -->
      <div v-else-if="history.length > 0">
        <!-- График динамики -->
        <div class="chart-card">
          <h2>Динамика показателей</h2>
          <line-chart 
            v-if="chartData.labels.length > 0" 
            :data="chartData" 
            :options="chartOptions" 
          />
        </div>
  
        <!-- Статистика -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon"></div>
            <div class="stat-content">
              <h3>Средний балл</h3>
              <p class="stat-value">{{ averageScore.toFixed(1) }}%</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon"></div>
            <div class="stat-content">
              <h3>Лучший результат</h3>
              <p class="stat-value">{{ maxScore.toFixed(1) }}%</p>
              <span class="stat-label">{{ maxScorePeriod }}</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon"></div>
            <div class="stat-content">
              <h3>Общая премия</h3>
              <p class="stat-value">{{ formatCurrency(totalBonus) }}</p>
              <span class="stat-label">За период</span>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon" :class="trendClass">
              {{ trendIcon }}
            </div>
            <div class="stat-content">
              <h3>Тренд</h3>
              <p class="stat-value" :class="trendClass">{{ trendText }}</p>
            </div>
          </div>
        </div>
  
        <!-- Таблица истории -->
        <div class="history-table-card">
          <h2>Детальная история</h2>
          <div class="table-responsive">
            <table class="history-table">
              <thead>
                <tr>
                  <th>Период</th>
                  <th>Общий балл</th>
                  <th>Уровень</th>
                  <th>Премия</th>
                  <th>Изменение</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in history" :key="index">
                  <td class="period-cell">
                    <strong>{{ formatPeriod(item.period) }}</strong>
                  </td>
                  <td class="score-cell">
                    <div class="score-badge" :class="getScoreClass(item.total_score)">
                      {{ item.total_score.toFixed(1) }}%
                    </div>
                  </td>
                  <td class="level-cell">
                    <span class="level-badge" :class="'level-' + item.performance_level">
                      {{ formatLevel(item.performance_level) }}
                    </span>
                  </td>
                  <td class="bonus-cell">
                    {{ formatCurrency(item.bonus_amount) }}
                  </td>
                  <td class="change-cell">
                    <span v-if="index < history.length - 1" 
                          :class="getChangeClass(item.total_score, history[index + 1].total_score)">
                      {{ getChangeText(item.total_score, history[index + 1].total_score) }}
                    </span>
                    <span v-else class="text-muted">—</span>
                  </td>
                  <td class="actions-cell">
                    <button 
                      @click="viewDetails(item.period)" 
                      class="btn-icon"
                      title="Просмотр деталей"
                    >
                      ️
                    </button>
                    <button 
                      @click="generateReport(item.period)" 
                      class="btn-icon"
                      title="Скачать отчет"
                    >
                      
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
  
        <!-- График по категориям -->
        <div class="categories-chart-card">
          <h2>Распределение по категориям</h2>
          <div class="categories-grid">
            <div v-for="(category, name) in categoryStats" :key="name" class="category-item">
              <h4>{{ name }}</h4>
              <div class="category-bar">
                <div 
                  class="category-fill" 
                  :style="{ width: category.average + '%' }"
                  :class="getScoreClass(category.average)"
                ></div>
              </div>
              <p class="category-value">{{ category.average.toFixed(1) }}%</p>
            </div>
          </div>
        </div>
      </div>
  
      <!-- Пустое состояние -->
      <div v-else class="empty-state">
        <div class="empty-icon"></div>
        <h2>История пуста</h2>
        <p>У вас пока нет данных за выбранный период</p>
        <router-link to="/" class="btn btn-primary">
          Перейти к дашборду
        </router-link>
      </div>
    </div>
  </template>
  
  <script>
  import LineChart from '@/components/charts/LineChart.vue';
  import { kpiAPI, downloadPDF } from '@/services/api';
  
  export default {
    name: 'HistoryView',
    components: {
      LineChart
    },
    data() {
      return {
        selectedMonths: 6,
        history: [],
        loading: false,
        chartData: {
          labels: [],
          datasets: [
            {
              label: 'Общий балл KPI',
              data: [],
              borderColor: '#3498db',
              backgroundColor: 'rgba(52, 152, 219, 0.1)',
              tension: 0.4,
              fill: true,
              pointRadius: 5,
              pointHoverRadius: 7
            }
          ]
        },
        chartOptions: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              min: 0,
              max: 100,
              title: {
                display: true,
                text: 'Баллы (%)'
              }
            }
          },
          plugins: {
            tooltip: {
              mode: 'index',
              intersect: false,
              callbacks: {
                label: (context) => {
                  return `Балл: ${context.parsed.y.toFixed(1)}%`;
                }
              }
            },
            legend: {
              display: true,
              position: 'top'
            }
          }
        }
      };
    },
    computed: {
      averageScore() {
        if (this.history.length === 0) return 0;
        const sum = this.history.reduce((acc, item) => acc + item.total_score, 0);
        return sum / this.history.length;
      },
      maxScore() {
        if (this.history.length === 0) return 0;
        return Math.max(...this.history.map(item => item.total_score));
      },
      maxScorePeriod() {
        if (this.history.length === 0) return '';
        const maxItem = this.history.reduce((prev, current) => 
          (prev.total_score > current.total_score) ? prev : current
        );
        return this.formatPeriod(maxItem.period);
      },
      totalBonus() {
        return this.history.reduce((acc, item) => acc + item.bonus_amount, 0);
      },
      trendIcon() {
        if (this.history.length < 2) return '➡️';
        const recent = this.history[0].total_score;
        const old = this.history[this.history.length - 1].total_score;
        if (recent > old) return '';
        if (recent < old) return '';
        return '➡️';
      },
      trendClass() {
        if (this.history.length < 2) return '';
        const recent = this.history[0].total_score;
        const old = this.history[this.history.length - 1].total_score;
        if (recent > old) return 'trend-up';
        if (recent < old) return 'trend-down';
        return 'trend-neutral';
      },
      trendText() {
        if (this.history.length < 2) return 'Недостаточно данных';
        const recent = this.history[0].total_score;
        const old = this.history[this.history.length - 1].total_score;
        const diff = recent - old;
        if (diff > 0) return `+${diff.toFixed(1)}%`;
        if (diff < 0) return `${diff.toFixed(1)}%`;
        return 'Без изменений';
      },
      categoryStats() {
        // Здесь можно добавить логику расчета по категориям
        // Пока возвращаем заглушку
        return {
          'Публикации': { average: 85.5 },
          'Проекты': { average: 72.3 },
          'Преподавание': { average: 90.1 }
        };
      }
    },
    async created() {
      await this.loadHistory();
    },
    methods: {
      async loadHistory() {
        this.loading = true;
        try {
          const response = await kpiAPI.getHistory(this.selectedMonths);
          this.history = response.data.reverse(); // От новых к старым
          this.updateChart();
        } catch (error) {
          console.error('Ошибка загрузки истории:', error);
          this.$toast.error('Не удалось загрузить историю KPI');
        } finally {
          this.loading = false;
        }
      },
      updateChart() {
        const reversed = [...this.history].reverse(); // От старых к новым для графика
        this.chartData.labels = reversed.map(item => this.formatPeriod(item.period));
        this.chartData.datasets[0].data = reversed.map(item => item.total_score);
      },
      formatPeriod(period) {
        const [year, month] = period.split('-');
        const monthNames = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                            'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
        return `${monthNames[parseInt(month) - 1]} ${year}`;
      },
      formatCurrency(amount) {
        return new Intl.NumberFormat('ru-RU', {
          style: 'currency',
          currency: 'RUB',
          minimumFractionDigits: 0
        }).format(amount);
      },
      formatLevel(level) {
        const levels = {
          'высокий': 'Высокая',
          'средний': 'Средняя',
          'низкий': 'Низкая'
        };
        return levels[level] || level;
      },
      getScoreClass(score) {
        if (score >= 90) return 'excellent';
        if (score >= 70) return 'good';
        if (score >= 50) return 'medium';
        return 'poor';
      },
      getChangeClass(current, previous) {
        const diff = current - previous;
        if (diff > 0) return 'change-positive';
        if (diff < 0) return 'change-negative';
        return 'change-neutral';
      },
      getChangeText(current, previous) {
        const diff = current - previous;
        if (diff > 0) return `+${diff.toFixed(1)}%`;
        if (diff < 0) return `${diff.toFixed(1)}%`;
        return '0%';
      },
      viewDetails(period) {
        this.$router.push(`/?period=${period}`);
      },
      async generateReport(period) {
        try {
          const response = await kpiAPI.generateReport(period);
          downloadPDF(response.data, `KPI_Report_${period}.pdf`);
          this.$toast.success('Отчет загружен');
        } catch (error) {
          console.error('Ошибка генерации отчета:', error);
          this.$toast.error('Не удалось сгенерировать отчет');
        }
      },
      exportToExcel() {
        // Заглушка для экспорта в Excel
        this.$toast.info('Функция экспорта в Excel в разработке');
      }
    }
  };
  </script>
  
  <style scoped>
  .history-container {
    max-width: 1400px;
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
  
  .controls {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .controls label {
    font-weight: 500;
    color: #555;
  }
  
  .controls select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: white;
    cursor: pointer;
  }
  
  /* График */
  .chart-card {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-bottom: 24px;
    height: 400px;
  }
  
  .chart-card h2 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #2c3e50;
  }
  
  /* Статистика */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 32px;
  }
  
  .stat-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .stat-icon {
    font-size: 2.5rem;
  }
  
  .stat-icon.trend-up {
    color: #27ae60;
  }
  
  .stat-icon.trend-down {
    color: #e74c3c;
  }
  
  .stat-content h3 {
    margin: 0 0 8px 0;
    font-size: 0.9rem;
    color: #7f8c8d;
    font-weight: 500;
  }
  
  .stat-value {
    margin: 0;
    font-size: 1.8rem;
    font-weight: bold;
    color: #2c3e50;
  }
  
  .stat-value.trend-up {
    color: #27ae60;
  }
  
  .stat-value.trend-down {
    color: #e74c3c;
  }
  
  .stat-label {
    font-size: 0.85rem;
    color: #95a5a6;
  }
  
  /* Таблица */
  .history-table-card {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-bottom: 24px;
  }
  
  .history-table-card h2 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #2c3e50;
  }
  
  .table-responsive {
    overflow-x: auto;
  }
  
  .history-table {
    width: 100%;
    border-collapse: collapse;
  }
  
  .history-table th {
    background: #f8f9fa;
    padding: 12px;
    text-align: left;
    font-weight: 600;
    color: #2c3e50;
    border-bottom: 2px solid #e9ecef;
  }
  
  .history-table td {
    padding: 12px;
    border-bottom: 1px solid #e9ecef;
  }
  
  .history-table tr:hover {
    background: #f8f9fa;
  }
  
  .score-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.95rem;
  }
  
  .score-badge.excellent {
    background: #d4edda;
    color: #155724;
  }
  
  .score-badge.good {
    background: #fff3cd;
    color: #856404;
  }
  
  .score-badge.medium {
    background: #ffe5d0;
    color: #8b4513;
  }
  
  .score-badge.poor {
    background: #f8d7da;
    color: #721c24;
  }
  
  .level-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;
  }
  
  .level-badge.level-высокий {
    background: #d4edda;
    color: #155724;
  }
  
  .level-badge.level-средний {
    background: #fff3cd;
    color: #856404;
  }
  
  .level-badge.level-низкий {
    background: #f8d7da;
    color: #721c24;
  }
  
  .change-positive {
    color: #27ae60;
    font-weight: 600;
  }
  
  .change-negative {
    color: #e74c3c;
    font-weight: 600;
  }
  
  .change-neutral {
    color: #95a5a6;
  }
  
  .text-muted {
    color: #95a5a6;
  }
  
  .btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 4px 8px;
    transition: transform 0.2s;
  }
  
  .btn-icon:hover {
    transform: scale(1.2);
  }
  
  /* Категории */
  .categories-chart-card {
    background: white;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .categories-chart-card h2 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #2c3e50;
  }
  
  .categories-grid {
    display: grid;
    gap: 16px;
  }
  
  .category-item h4 {
    margin: 0 0 8px 0;
    color: #2c3e50;
  }
  
  .category-bar {
    height: 24px;
    background: #e9ecef;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 4px;
  }
  
  .category-fill {
    height: 100%;
    transition: width 0.5s ease;
  }
  
  .category-fill.excellent {
    background: #27ae60;
  }
  
  .category-fill.good {
    background: #f39c12;
  }
  
  .category-fill.medium {
    background: #e67e22;
  }
  
  .category-fill.poor {
    background: #e74c3c;
  }
  
  .category-value {
    margin: 0;
    font-size: 0.9rem;
    color: #7f8c8d;
  }
  
  /* Состояния */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    color: #7f8c8d;
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
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    text-align: center;
  }
  
  .empty-icon {
    font-size: 4rem;
    margin-bottom: 16px;
    opacity: 0.5;
  }
  
  .empty-state h2 {
    color: #2c3e50;
    margin-bottom: 8px;
  }
  
  .empty-state p {
    color: #7f8c8d;
    margin-bottom: 24px;
  }
  
  /* Кнопки */
  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: opacity 0.2s;
    text-decoration: none;
    display: inline-block;
  }
  
  .btn:hover {
    opacity: 0.9;
  }
  
  .btn-primary {
    background: #3498db;
    color: white;
  }
  
  .btn-secondary {
    background: #95a5a6;
    color: white;
  }
  </style>