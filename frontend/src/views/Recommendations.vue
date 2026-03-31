<template>
  <div class="rec-page">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1>Рекомендации по улучшению</h1>
        <p class="page-subtitle">
          Персональные рекомендации на основе анализа ваших показателей KPI
        </p>
      </div>
      <div class="header-controls">
        <select v-model="selectedPeriod" @change="loadData" class="period-select">
          <option v-for="p in periods" :key="p" :value="p">{{ formatPeriod(p) }}</option>
        </select>
        <button @click="refreshData" class="btn btn-outline" :disabled="loading">
          Обновить
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка рекомендаций...</p>
    </div>

    <template v-else>
      <!-- Summary cards -->
      <div v-if="allRecommendations.length > 0" class="summary-row">
        <div class="summary-card" :class="{ active: filter === 'all' }" @click="filter = 'all'">
          <div class="summary-num">{{ allRecommendations.length }}</div>
          <div class="summary-label">Всего</div>
        </div>
        <div class="summary-card high" :class="{ active: filter === 'high' }" @click="filter = 'high'">
          <div class="summary-num">{{ highCount }}</div>
          <div class="summary-label">Высокий приоритет</div>
        </div>
        <div class="summary-card medium" :class="{ active: filter === 'medium' }" @click="filter = 'medium'">
          <div class="summary-num">{{ mediumCount }}</div>
          <div class="summary-label">Средний приоритет</div>
        </div>
        <div class="summary-card low" :class="{ active: filter === 'low' }" @click="filter = 'low'">
          <div class="summary-num">{{ lowCount }}</div>
          <div class="summary-label">Низкий приоритет</div>
        </div>
        <div class="summary-card done" :class="{ active: filter === 'completed' }" @click="filter = 'completed'">
          <div class="summary-num">{{ completedCount }}</div>
          <div class="summary-label">Выполнено</div>
        </div>
      </div>

      <!-- Recommendations list -->
      <div v-if="filteredRecommendations.length > 0" class="rec-list">
        <div
          v-for="rec in filteredRecommendations"
          :key="rec.id"
          class="rec-card"
          :class="[
            `priority-${rec.priority}`,
            { completed: rec.is_completed }
          ]"
        >
          <!-- Left: priority stripe is done via CSS border-left -->
          <div class="rec-main">
            <!-- Top row -->
            <div class="rec-top">
              <div class="rec-title-row">
                <span class="priority-tag" :class="rec.priority">
                  {{ priorityLabel(rec.priority) }}
                </span>
                <h3 class="rec-indicator">{{ rec.indicator_name }}</h3>
                <span v-if="rec.indicator_group" class="rec-group">{{ rec.indicator_group }}</span>
              </div>
              <span v-if="rec.is_completed" class="done-badge">Выполнено</span>
            </div>

            <!-- Progress -->
            <div class="rec-progress-row">
              <div class="progress-track">
                <div
                  class="progress-fill"
                  :class="progressClass(rec.current_completion)"
                  :style="{ width: Math.min(rec.current_completion, 100) + '%' }"
                ></div>
              </div>
              <div class="progress-numbers">
                <span class="progress-pct" :class="progressClass(rec.current_completion)">
                  {{ rec.current_completion.toFixed(0) }}%
                </span>
                <span class="progress-detail">
                  {{ rec.actual_value }} / {{ rec.target_value }} {{ rec.indicator_unit }}
                </span>
              </div>
            </div>

            <!-- Text -->
            <p class="rec-text">{{ rec.text }}</p>

            <!-- Bottom row -->
            <div class="rec-bottom">
              <div class="rec-meta">
                <span class="meta-item" v-if="rec.deadline_period">
                  Срок: <strong>{{ formatPeriod(rec.deadline_period) }}</strong>
                </span>
                <span class="meta-item">
                  Осталось: <strong>{{ (rec.target_value - rec.actual_value).toFixed(1) }} {{ rec.indicator_unit }}</strong>
                </span>
              </div>
              <div class="rec-actions">
                <button
                  v-if="!rec.is_completed"
                  @click="completeRec(rec.id)"
                  class="btn btn-success btn-sm"
                >
                  Выполнено
                </button>
                <button
                  v-else
                  @click="uncompleteRec(rec.id)"
                  class="btn btn-outline btn-sm"
                >
                  Вернуть
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="allRecommendations.length === 0" class="empty-state">
        <h2>Нет рекомендаций за этот период</h2>
        <p v-if="filter === 'all'">Все показатели выполняются на достаточном уровне</p>
        <p v-else>Нет рекомендаций с выбранным фильтром. <a href="#" @click.prevent="filter = 'all'">Показать все</a></p>
      </div>

      <!-- Filtered empty -->
      <div v-else-if="filteredRecommendations.length === 0" class="empty-state">
        <p>Нет рекомендаций с выбранным фильтром.</p>
        <a href="#" @click.prevent="filter = 'all'">Показать все</a>
      </div>
    </template>
  </div>
</template>

<script>
import { kpiAPI } from '@/services/api';
import { formatPeriod } from '@/utils/formatters';

export default {
  name: 'RecommendationsView',
  data() {
    return {
      allRecommendations: [],
      periods: [],
      selectedPeriod: '',
      filter: 'all', // all | high | medium | low | completed
      loading: false,
    };
  },
  computed: {
    filteredRecommendations() {
      if (this.filter === 'all') return this.allRecommendations.filter(r => !r.is_completed);
      if (this.filter === 'completed') return this.allRecommendations.filter(r => r.is_completed);
      return this.allRecommendations.filter(r => !r.is_completed && r.priority === this.filter);
    },
    highCount() { return this.allRecommendations.filter(r => !r.is_completed && r.priority === 'high').length; },
    mediumCount() { return this.allRecommendations.filter(r => !r.is_completed && r.priority === 'medium').length; },
    lowCount() { return this.allRecommendations.filter(r => !r.is_completed && r.priority === 'low').length; },
    completedCount() { return this.allRecommendations.filter(r => r.is_completed).length; },
  },
  async created() {
    await this.loadPeriods();
    await this.loadData();
  },
  methods: {
    async loadPeriods() {
      try {
        const response = await kpiAPI.getPeriods();
        this.periods = Array.isArray(response.data) ? response.data : [];
        if (this.periods.length > 0 && !this.selectedPeriod) {
          this.selectedPeriod = this.periods[0];
        }
      } catch {
        // Fallback: use current month
        const now = new Date();
        this.selectedPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
        this.periods = [this.selectedPeriod];
      }
    },

    async loadData() {
      if (!this.selectedPeriod) return;
      this.loading = true;
      try {
        const response = await kpiAPI.getRecommendations(this.selectedPeriod);
        this.allRecommendations = response.data || [];
      } catch (error) {
        console.error('Ошибка загрузки рекомендаций:', error);
        this.$toast.error('Не удалось загрузить рекомендации');
      } finally {
        this.loading = false;
      }
    },

    async refreshData() {
      await this.loadData();
      this.$toast.success('Рекомендации обновлены');
    },

    async completeRec(id) {
      try {
        await kpiAPI.completeRecommendation(id);
        const rec = this.allRecommendations.find(r => r.id === id);
        if (rec) rec.is_completed = true;
        this.$toast.success('Рекомендация отмечена как выполненная');
      } catch {
        this.$toast.error('Не удалось обновить рекомендацию');
      }
    },

    async uncompleteRec(id) {
      try {
        await kpiAPI.uncompleteRecommendation(id);
        const rec = this.allRecommendations.find(r => r.id === id);
        if (rec) rec.is_completed = false;
        this.$toast.success('Рекомендация возвращена в активные');
      } catch {
        this.$toast.error('Не удалось обновить рекомендацию');
      }
    },

    priorityLabel(p) {
      return { high: 'Высокий', medium: 'Средний', low: 'Низкий' }[p] || p;
    },

    progressClass(val) {
      if (val >= 60) return 'ok';
      if (val >= 30) return 'warn';
      return 'crit';
    },

    formatPeriod,
  },
};
</script>

<style scoped>
.rec-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  gap: 16px;
}

.page-header h1 { margin: 0 0 4px; color: #1a202c; font-size: 1.5rem; }
.page-subtitle { margin: 0; color: #6b7280; font-size: 0.95rem; }

.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

.period-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
}

/* Summary row */
.summary-row {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.summary-card {
  flex: 1;
  min-width: 130px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
}

.summary-card:hover { border-color: #9ca3af; }
.summary-card.active { border-color: #3b82f6; background: #eff6ff; }

.summary-card.high .summary-num { color: #dc2626; }
.summary-card.medium .summary-num { color: #d97706; }
.summary-card.low .summary-num { color: #059669; }
.summary-card.done .summary-num { color: #6b7280; }

.summary-num {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1a202c;
  line-height: 1;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 500;
}

/* Recommendation list */
.rec-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rec-card {
  background: white;
  border-radius: 8px;
  border-left: 4px solid #d1d5db;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  transition: box-shadow 0.15s;
}

.rec-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }

.rec-card.priority-high { border-left-color: #dc2626; }
.rec-card.priority-medium { border-left-color: #d97706; }
.rec-card.priority-low { border-left-color: #059669; }
.rec-card.completed { opacity: 0.55; border-left-color: #9ca3af; }

.rec-main { padding: 18px 20px; }

/* Top row */
.rec-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.rec-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.priority-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.priority-tag.high { background: #fef2f2; color: #dc2626; }
.priority-tag.medium { background: #fffbeb; color: #d97706; }
.priority-tag.low { background: #ecfdf5; color: #059669; }

.rec-indicator {
  margin: 0;
  font-size: 1.05rem;
  color: #1a202c;
}

.rec-group {
  font-size: 0.82rem;
  color: #9ca3af;
}

.done-badge {
  padding: 3px 10px;
  background: #d1fae5;
  color: #065f46;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
}

/* Progress */
.rec-progress-row {
  margin-bottom: 12px;
}

.progress-track {
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.progress-fill.ok { background: #059669; }
.progress-fill.warn { background: #d97706; }
.progress-fill.crit { background: #dc2626; }

.progress-numbers {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
}

.progress-pct { font-weight: 700; }
.progress-pct.ok { color: #059669; }
.progress-pct.warn { color: #d97706; }
.progress-pct.crit { color: #dc2626; }

.progress-detail { color: #6b7280; }

/* Text */
.rec-text {
  margin: 0 0 14px;
  color: #374151;
  line-height: 1.6;
  font-size: 0.93rem;
}

/* Bottom */
.rec-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.rec-meta {
  display: flex;
  gap: 20px;
  font-size: 0.85rem;
  color: #6b7280;
}

.rec-actions {
  display: flex;
  gap: 8px;
}

/* Кнопки — глобальные стили в App.vue */
.btn-success { background: #10b981; color: white; }

/* States */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  color: #6b7280;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-state h2 { color: #059669; margin-bottom: 8px; }
.empty-state a { color: #3b82f6; }

/* Responsive */
@media (max-width: 768px) {
  .page-header { flex-direction: column; }
  .summary-row { flex-direction: column; }
  .summary-card { min-width: auto; }
  .rec-bottom { flex-direction: column; align-items: flex-start; }
  .rec-meta { flex-direction: column; gap: 4px; }
}
</style>
