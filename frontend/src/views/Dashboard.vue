<template>
  <div class="dashboard-container">
    <div class="header">
      <h1>Ваш персональный дашборд KPI</h1>
      <div v-if="availablePeriods.length > 0" class="period-selector">
        <label for="period">Период:</label>
        <select id="period" v-model="selectedPeriod" @change="loadData">
          <option v-for="period in availablePeriods" :key="period" :value="period">
            {{ formatDate(period) }}
          </option>
        </select>
      </div>
    </div>
    
    <div class="summary-cards">
      <div class="card total-score">
        <h3>Общий балл KPI</h3>
        <div class="score-value" :class="scoreClass">
          {{ totalScore.toFixed(1) }}
        </div>
        <div class="performance-level">
          <span :class="['badge', performanceLevelClass]">
            {{ performanceLevelText }}
          </span>
        </div>
        <div class="bonus-info">
          <p>Потенциальная премия: <strong>{{ formatCurrency(bonusAmount) }}</strong></p>
          <p class="trend" :class="trendClass">
            {{ trendText }}
          </p>
        </div>
      </div>
      
      <div class="card progress-overview">
        <h3>Динамика показателей</h3>
        <line-chart v-if="chartData.labels.length > 0" :data="chartData" :options="chartOptions" />
        <p v-else>Загрузка данных для графика...</p>
      </div>
    </div>
    
    <div class="kpi-groups">
      <div v-for="(group, index) in kpiGroups" :key="index" class="group-card">
        <div class="group-header" @click="toggleGroup(index)">
          <h3>{{ group.name }}</h3>
          <div class="group-score">
            <span class="score">{{ group.score.toFixed(1) }}%</span>
            <span class="progress-indicator" :class="getProgressClass(group.score)"></span>
          </div>
          <span class="toggle-icon">{{ expandedGroups[index] ? '−' : '+' }}</span>
        </div>
        
        <div v-if="expandedGroups[index]" class="group-details">
          <div v-for="(indicator, idx) in group.indicators" :key="idx" class="indicator-item">
            <div class="indicator-name">{{ indicator.name }}</div>
            <div class="indicator-progress">
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: indicator.completion_percent + '%'}"
                  :class="getProgressClass(indicator.completion_percent)"
                ></div>
              </div>
              <div class="progress-text">
                {{ indicator.actual_value.toFixed(1) }} / {{ indicator.target_value.toFixed(1) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="recommendations" v-if="recommendations.length > 0">
      <h2>Рекомендации по улучшению</h2>
      <div v-for="(rec, index) in recommendations" :key="index" class="recommendation-card">
        <div class="rec-header">
          <h3>{{ rec.indicator_name }}</h3>
          <span class="badge warning">Требует внимания</span>
        </div>
        <p>{{ rec.text }}</p>
        <div class="rec-footer">
          <span class="target">Цель до {{ rec.deadline_period }}: {{ rec.target_value }}</span>
          <button @click="markRecommendationDone(rec.id)" class="btn btn-sm btn-outline">
            Отметить как выполненное
          </button>
        </div>
      </div>
    </div>
    
    <div class="actions">
      <button @click="generateReport" class="btn btn-primary">
        Сформировать отчет в PDF
      </button>
      <button @click="showDataInputModal" class="btn btn-secondary">
        Добавить данные
      </button>
    </div>
    
    <data-input-modal 
      v-if="showModal"
      @close="showModal = false"
      @data-saved="loadData"
    /> 
  </div>
</template>

<script>
import LineChart from '@/components/charts/LineChart.vue';
import DataInputModal from '@/components/DataInputModal.vue';
import { kpiAPI, downloadPDF } from '@/services/api';

export default {
  name: 'DashboardView',
  components: {
    LineChart,
    DataInputModal
  },
  data() {
    return {
      selectedPeriod: '',
      availablePeriods: [],
      totalScore: 0,
      previousScore: 0,
      performanceLevel: 'низкий',
      bonusAmount: 0,
      kpiGroups: [],
      expandedGroups: [],
      recommendations: [],
      showModal: false,
      chartData: {
        labels: [],
        datasets: [{
          label: 'Общий балл KPI',
          data: [],
          borderColor: '#3e95cd',
          backgroundColor: 'rgba(62, 149, 205, 0.1)',
          tension: 0.3,
          fill: true
        }]
      },
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { min: 0, max: 100, title: { display: true, text: 'Баллы' } } },
        plugins: { tooltip: { mode: 'index', intersect: false } }
      }
    };
  },
  computed: {
    scoreClass() {
      if (this.totalScore >= 90) return 'excellent';
      if (this.totalScore >= 70) return 'good';
      return 'needs-improvement';
    },
    performanceLevelClass() {
      return `level-${this.performanceLevel}`;
    },
    performanceLevelText() {
      const levels = {
        'высокий': 'Высокая эффективность',
        'средний': 'Средняя эффективность',
        'низкий': 'Низкая эффективность'
      };
      return levels[this.performanceLevel] || 'Не определено';
    },
    trendText() {
      const diff = this.totalScore - this.previousScore;
      if (diff > 0) return `↑ +${diff.toFixed(1)} балла по сравнению с прошлым периодом`;
      if (diff < 0) return `↓ ${diff.toFixed(1)} балла по сравнению с прошлым периодом`;
      return 'Без изменений по сравнению с прошлым периодом';
    },
    trendClass() {
      const diff = this.totalScore - this.previousScore;
      if (diff > 0) return 'positive';
      if (diff < 0) return 'negative';
      return 'neutral';
    }
  },
  async created() {
    await this.loadPeriods();
  },
  methods: {
    async loadPeriods() {
      try {
        const response = await kpiAPI.getPeriods();
        this.availablePeriods = response.data;
        if (this.availablePeriods.length > 0) {
          const now = new Date();
          const currentPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
          this.selectedPeriod = this.availablePeriods.includes(currentPeriod) 
            ? currentPeriod 
            : this.availablePeriods[0];
          await this.loadData();
        }
      } catch (error) {
        console.error('Ошибка загрузки периодов:', error);
        this.$toast.error('Не удалось загрузить список периодов');
      }
    },
    async loadData() {
      if (!this.selectedPeriod) return;
      try {
        this.$toast.info('Загрузка данных...');
        const response = await kpiAPI.getDashboard(this.selectedPeriod);
        const data = response.data;
        
        this.totalScore = data.total_score;
        this.performanceLevel = data.performance_level;
        this.bonusAmount = data.bonus_amount;
        this.kpiGroups = Object.values(data.group_scores);
        this.expandedGroups = Array(this.kpiGroups.length).fill(true);
        
        await this.loadPreviousPeriodData();
        await this.loadRecommendations();
        await this.loadChartData();
        
        this.$toast.success('Данные успешно загружены');
      } catch (error) {
        console.error('Ошибка загрузки данных дашборда:', error);
        this.$toast.error('Не удалось загрузить данные дашборда');
      }
    },
    async loadPreviousPeriodData() {
      try {
        const [year, month] = this.selectedPeriod.split('-');
        let prevYear = parseInt(year);
        let prevMonth = parseInt(month) - 1;
        if (prevMonth === 0) {
          prevMonth = 12;
          prevYear -= 1;
        }
        const prevPeriod = `${prevYear}-${String(prevMonth).padStart(2, '0')}`;
        const response = await kpiAPI.getDashboard(prevPeriod);
        this.previousScore = response.data.total_score;
      } catch (error) {
        this.previousScore = 0;
      }
    },
    async loadRecommendations() {
      try {
        const response = await kpiAPI.getRecommendations(this.selectedPeriod);
        this.recommendations = response.data;
      } catch (error) {
        console.error('Ошибка загрузки рекомендаций:', error);
      }
    },
    async loadChartData() {
      try {
        const response = await kpiAPI.getHistory(6);
        if (response.data && Array.isArray(response.data)) {
          const history = response.data.reverse();
          this.chartData.labels = history.map(item => this.formatDate(item.period));
          this.chartData.datasets[0].data = history.map(item => item.total_score);
        } else {
          this.chartData.labels = [];
          this.chartData.datasets[0].data = [];
        }
      } catch (error) {
        console.error('Ошибка загрузки истории KPI:', error);
        this.chartData.labels = [];
        this.chartData.datasets[0].data = [];
      }
    },
    toggleGroup(index) {
      this.expandedGroups[index] = !this.expandedGroups[index];
    },
    getProgressClass(value) {
      if (value >= 90) return 'excellent';
      if (value >= 70) return 'good';
      if (value >= 50) return 'medium';
      return 'poor';
    },
    formatDate(period) {
      const [year, month] = period.split('-');
      const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
      return `${monthNames[parseInt(month) - 1]} ${year}`;
    },
    formatCurrency(amount) {
      return new Intl.NumberFormat('ru-RU', { 
        style: 'currency', 
        currency: 'RUB', 
        minimumFractionDigits: 0, 
        maximumFractionDigits: 0 
      }).format(amount);
    },
    async generateReport() {
      try {
        const response = await kpiAPI.generateReport(this.selectedPeriod);
        const filename = `KPI_Report_${this.selectedPeriod}.pdf`;
        downloadPDF(response.data, filename);
        this.$toast.success('Отчет сформирован и загружен');
      } catch (error) {
        console.error('Ошибка генерации отчета:', error);
        this.$toast.error('Не удалось сгенерировать отчет');
      }
    },
    showDataInputModal() {
      this.showModal = true;
    },
    async markRecommendationDone(recId) {
      try {
        await kpiAPI.completeRecommendation(recId);
        this.$toast.success('Рекомендация отмечена как выполненная');
        await this.loadRecommendations();
      } catch (error) {
        console.error('Ошибка отметки рекомендации:', error);
        this.$toast.error('Не удалось отметить рекомендацию');
      }
    }
  }
};
</script>

<style scoped>
.dashboard-container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.summary-cards { display: grid; grid-template-columns: 1fr 2fr; gap: 24px; margin-bottom: 32px; }
.card { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); padding: 20px; }
.progress-overview { min-height: 300px; }
.total-score { text-align: center; }
.score-value { font-size: 3.5rem; font-weight: bold; margin: 16px 0; transition: color 0.3s ease; }
.score-value.excellent { color: #28a745; }
.score-value.good { color: #ffc107; }
.score-value.needs-improvement { color: #dc3545; }
.badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 500; }
.badge.level-высокий { background-color: #d4edda; color: #155724; }
.badge.level-средний { background-color: #fff3cd; color: #856404; }
.badge.level-низкий { background-color: #f8d7da; color: #721c24; }
.badge.warning { background-color: #fff3cd; color: #856404; }
.trend { margin-top: 8px; font-size: 0.9rem; }
.trend.positive { color: #28a745; }
.trend.negative { color: #dc3545; }
.trend.neutral { color: #6c757d; }
.group-card { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 16px; overflow: hidden; }
.group-header { display: flex; justify-content: space-between; align-items: center; padding: 16px; background-color: #f8f9fa; cursor: pointer; transition: background-color 0.2s ease; }
.group-header:hover { background-color: #e9ecef; }
.group-score { display: flex; align-items: center; gap: 8px; }
.progress-indicator { width: 12px; height: 12px; border-radius: 50%; }
.progress-indicator.excellent { background-color: #28a745; }
.progress-indicator.good { background-color: #ffc107; }
.progress-indicator.medium { background-color: #fd7e14; }
.progress-indicator.poor { background-color: #dc3545; }
.toggle-icon { font-weight: bold; font-size: 1.2rem; }
.group-details { padding: 16px; border-top: 1px solid #e9ecef; }
.indicator-item { margin-bottom: 12px; }
.indicator-name { font-weight: 500; margin-bottom: 4px; }
.indicator-progress { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.progress-bar { flex: 1; height: 8px; background-color: #e9ecef; border-radius: 4px; }
.progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.progress-fill.excellent { background-color: #28a745; }
.progress-fill.good { background-color: #ffc107; }
.progress-fill.medium { background-color: #fd7e14; }
.progress-fill.poor { background-color: #dc3545; }
.progress-text { font-size: 0.9rem; white-space: nowrap; }
.recommendations { margin: 32px 0; }
.recommendation-card { background: white; border-left: 4px solid #ffc107; border-radius: 4px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); }
.rec-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.rec-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
.target { color: #6c757d; font-size: 0.9rem; }
.actions { display: flex; gap: 12px; margin-top: 24px; }
.btn { padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer; font-weight: 500; transition: all 0.2s ease; }
.btn-primary { background-color: #007bff; color: white; }
.btn-secondary { background-color: #6c757d; color: white; }
.btn:hover { opacity: 0.9; }
.btn-outline { background-color: transparent; border: 1px solid #6c757d; color: #6c757d; }
</style>