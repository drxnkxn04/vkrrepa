<template>
  <div class="dashboard-container">
    <!-- Шапка с кнопками действий -->
    <div class="header">
      <div class="header-left">
        <h1>Ваш персональный дашборд KPI</h1>
        <div v-if="availablePeriods.length > 0" class="period-selector">
          <label for="period">Период:</label>
          <select id="period" v-model="selectedPeriod" @change="loadData">
            <option v-for="p in availablePeriods" :key="p" :value="p">
              {{ formatDate(p) }}
            </option>
          </select>
        </div>
      </div>
      <div class="header-actions">
        <button @click="showDataInputModal" class="btn btn-primary">
          + Добавить данные
        </button>
        <button @click="generateReport" class="btn btn-outline-primary">
          Скачать PDF
        </button>
        <button @click="generateExcel" class="btn btn-outline-excel">
          Скачать Excel
        </button>
      </div>
    </div>

    <!-- Предупреждения о порогах -->
    <div v-if="thresholdWarnings.length > 0" class="threshold-warnings">
      <div v-for="(warn, i) in thresholdWarnings" :key="i" class="threshold-warning">
        <span class="warn-icon">&#9888;</span>
        <span>{{ warn.group_name }}: набрано {{ warn.current_points }} из минимума {{ warn.min_threshold }} б. (дефицит {{ warn.deficit }} б.)</span>
      </div>
    </div>

    <!-- Блок «Что нужно сделать» -->
    <div v-if="actionItems.length > 0" class="action-panel">
      <h3>Требуется внимание</h3>
      <div class="action-items">
        <div
          v-for="(item, i) in actionItems"
          :key="i"
          class="action-item"
          :class="item.type"
        >
          <div class="action-text">
            <strong>{{ item.title }}</strong>
            <span>{{ item.description }}</span>
          </div>
          <button v-if="item.action" class="btn btn-sm btn-outline" @click="item.action">
            {{ item.buttonText }}
          </button>
        </div>
      </div>
    </div>

    <!-- Сводные карточки -->
    <div class="summary-cards">
      <div class="card total-score">
        <h3>Общий балл KPI</h3>
        <template v-if="dataLoading">
          <div class="score-skeleton"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </template>
        <template v-else>
          <div class="score-value" :class="scoreClass">
            {{ totalScore.toFixed(1) }}%
          </div>
          <div v-if="maxPoints > 0" class="points-info">
            {{ totalPoints.toFixed(0) }} / {{ maxPoints.toFixed(0) }} баллов
          </div>
          <div class="performance-level">
            <span :class="['badge', performanceLevelClass]">
              {{ performanceLevelText }}
            </span>
            <span v-if="userRole" class="badge role-badge">{{ userRole === 'rop' ? 'РОП' : 'ППС' }}</span>
          </div>
          <div class="bonus-info">
            <p>Бонус к ставке: <strong :class="bonusAmount >= 0 ? 'bonus-positive' : 'bonus-negative'">{{ bonusAmount >= 0 ? '+' : '' }}{{ formatCurrency(bonusAmount) }}</strong></p>
            <p class="trend" :class="trendClass">{{ trendText }}</p>
          </div>
        </template>
      </div>

      <div class="card progress-overview">
        <h3>Динамика показателей</h3>
        <line-chart v-if="chartData.labels.length > 0" :data="chartData" :options="chartOptions" />
        <p v-else class="empty-chart">Недостаточно данных для графика</p>
      </div>
    </div>

    <!-- Сравнение с командой -->
    <div v-if="teamAverage !== null" class="team-compare-card">
      <div class="tc-item">
        <span class="tc-label">Мой балл</span>
        <span class="tc-value" :class="scoreClass">{{ totalScore.toFixed(1) }}%</span>
        <div class="tc-bar-wrap">
          <div class="tc-bar">
            <div class="tc-fill mine" :style="{ width: Math.min(totalScore, 100) + '%' }"></div>
          </div>
        </div>
      </div>
      <div class="tc-divider">
        <span class="tc-diff" :class="diffClass">
          {{ diffText }}
        </span>
      </div>
      <div class="tc-item">
        <span class="tc-label">Среднее по команде</span>
        <span class="tc-value neutral">{{ teamAverage.toFixed(1) }}%</span>
        <div class="tc-bar-wrap">
          <div class="tc-bar">
            <div class="tc-fill team" :style="{ width: Math.min(teamAverage, 100) + '%' }"></div>
          </div>
        </div>
      </div>
      <div class="tc-meta">{{ teamUserCount }} сотрудников · {{ selectedPeriod ? formatDate(selectedPeriod) : '' }}</div>
    </div>

    <!-- Мои достижения за период -->
    <div class="values-section">
      <div class="section-header">
        <h2>Мои достижения за период</h2>
        <span class="period-label">{{ selectedPeriod ? formatDate(selectedPeriod) : '' }}</span>
      </div>
      <div v-if="valuesLoading" class="values-loading">Загрузка...</div>
      <div v-else-if="values.length > 0" class="values-table-wrap">
        <table class="values-table">
          <thead>
            <tr>
              <th>Показатель</th>
              <th>Факт</th>
              <th>План</th>
              <th>Статус</th>
              <th>Комментарий проверки</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="value in values" :key="value.id">
              <td>
                <div class="indicator-cell">
                  <span class="indicator-name">{{ value.indicator?.name || '—' }}</span>
                  <span class="indicator-group">{{ value.indicator?.group?.name || '' }}</span>
                </div>
              </td>
              <td class="value-cell">{{ value.actual_value }}</td>
              <td class="value-cell muted">{{ value.target_value }}</td>
              <td>
                <span class="status-badge" :class="statusClass(value.status)">
                  {{ formatStatus(value.status) }}
                </span>
              </td>
              <td class="comment-cell">{{ value.review_comment || '—' }}</td>
              <td>
                <div class="action-buttons">
                  <button
                    v-if="canEdit(value)"
                    class="btn btn-sm btn-edit"
                    @click="openEditModal(value)"
                    title="Редактировать"
                  >
                    Редактировать
                  </button>
                  <button
                    v-if="canSubmit(value)"
                    class="btn btn-sm btn-submit"
                    @click="submitValue(value)"
                    title="Отправить на проверку"
                  >
                    На проверку
                  </button>
                  <button
                    class="btn btn-sm btn-outline"
                    @click="openLogs(value)"
                    title="История изменений"
                  >
                    История
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="values-empty">
        <span>Нет данных за выбранный период.</span>
        <button @click="showDataInputModal" class="btn btn-sm btn-primary" style="margin-left:12px">
          + Добавить
        </button>
      </div>
    </div>

    <!-- KPI по группам -->
    <div class="kpi-groups-section">
      <h2>Показатели по направлениям</h2>
      <div class="groups-grid">
        <div
          v-for="(group, index) in kpiGroups"
          :key="index"
          class="group-card"
          :class="getProgressClass(group.score)"
        >
          <div class="group-card-header" @click="toggleGroup(index)">
            <div class="group-card-title">
              <span class="group-dot" :class="getProgressClass(group.score)"></span>
              <span>{{ group.name }}</span>
            </div>
            <div class="group-card-score">
              <span class="score-num" :class="getProgressClass(group.score)">{{ group.score.toFixed(0) }}%</span>
              <span v-if="group.max_points" class="group-points">{{ (group.points || 0).toFixed(0) }}/{{ group.max_points.toFixed(0) }} б.</span>
              <span class="toggle-btn">{{ expandedGroups[index] ? '▲' : '▼' }}</span>
            </div>
          </div>
          <div class="group-score-bar">
            <div
              class="group-score-fill"
              :class="getProgressClass(group.score)"
              :style="{ width: Math.min(group.score, 100) + '%' }"
            ></div>
          </div>
          <div v-if="expandedGroups[index]" class="group-indicators">
            <div v-for="(ind, idx) in group.indicators" :key="idx" class="ind-row">
              <div class="ind-name">{{ ind.name }}</div>
              <div class="ind-bar-wrap">
                <div class="ind-bar">
                  <div
                    class="ind-bar-fill"
                    :class="getProgressClass(ind.completion_percent)"
                    :style="{ width: Math.min(ind.completion_percent, 100) + '%' }"
                  ></div>
                </div>
                <span class="ind-values">{{ ind.actual_value.toFixed(1) }} / {{ ind.target_value.toFixed(1) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Рекомендации (компактный блок) -->
    <div class="rec-summary-block" v-if="activeRecommendations.length > 0">
      <div class="rec-summary-inner">
        <div class="rec-summary-left">
          <h3>Рекомендации по улучшению</h3>
          <div class="rec-summary-counts">
            <span v-if="recHighCount" class="rec-count high">{{ recHighCount }} высокий</span>
            <span v-if="recMediumCount" class="rec-count medium">{{ recMediumCount }} средний</span>
            <span v-if="recLowCount" class="rec-count low">{{ recLowCount }} низкий</span>
          </div>
          <p class="rec-summary-hint">
            {{ activeRecommendations.length }} {{ activeRecommendations.length === 1 ? 'показатель требует' : 'показателей требуют' }} внимания
          </p>
        </div>
        <router-link to="/recommendations" class="btn btn-primary btn-rec-link">
          Подробнее
        </router-link>
      </div>
    </div>

    <!-- Модалка истории изменений -->
    <div v-if="showLogsModal" class="modal-backdrop" @click.self="showLogsModal = false">
      <div class="logs-modal">
        <div class="logs-header">
          <h3>История изменений</h3>
          <button class="close-btn" @click="showLogsModal = false">&times;</button>
        </div>
        <div v-if="logsLoading" class="logs-loading">Загрузка...</div>
        <div v-else-if="valueLogs.length === 0" class="logs-empty">Нет записей</div>
        <div v-else class="logs-timeline">
          <div
            v-for="log in valueLogs"
            :key="log.id"
            class="log-entry"
            :class="log.action"
          >
            <div class="log-dot"></div>
            <div class="log-content">
              <div class="log-action">{{ log.action_display }}</div>
              <div class="log-meta">
                <span class="log-actor">{{ log.actor_name || 'Система' }}</span>
                <span class="log-time">{{ formatDateTime(log.created_at) }}</span>
              </div>
              <div v-if="log.old_value != null && log.new_value != null && log.old_value !== log.new_value" class="log-values">
                {{ log.old_value }} → {{ log.new_value }}
              </div>
              <div v-if="log.comment" class="log-comment">{{ log.comment }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <data-input-modal
      v-if="showModal"
      :edit-value="editingValue"
      @close="closeModal"
      @data-saved="loadData"
    />
  </div>
</template>

<script>
import LineChart from '@/components/charts/LineChart.vue';
import DataInputModal from '@/components/DataInputModal.vue';
import { kpiAPI, downloadPDF, extractResults } from '@/services/api';
import { formatPeriod, formatCurrency } from '@/utils/formatters';

export default {
  name: 'DashboardView',
  components: { LineChart, DataInputModal },
  data() {
    return {
      selectedPeriod: '',
      availablePeriods: [],
      dataLoading: true,
      totalScore: 0,
      totalPoints: 0,
      maxPoints: 0,
      previousScore: 0,
      performanceLevel: 'низкий',
      bonusAmount: 0,
      userRole: 'pps',
      thresholdWarnings: [],
      kpiGroups: [],
      expandedGroups: [],
      recommendations: [],
      values: [],
      valuesLoading: false,
      showModal: false,
      editingValue: null,
      showLogsModal: false,
      valueLogs: [],
      logsLoading: false,
      teamAverage: null,
      teamUserCount: 0,
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
    actionItems() {
      const items = [];
      // Отклонённые записи — нужно исправить
      const rejected = this.values.filter(v => v.status === 'rejected');
      if (rejected.length > 0) {
        items.push({
          type: 'rejected',
          title: `${rejected.length} ${rejected.length === 1 ? 'запись отклонена' : 'записей отклонено'}`,
          description: 'Исправьте данные и отправьте повторно',
          buttonText: 'Исправить',
          action: () => {
            const el = this.$el.querySelector('.values-section');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          },
        });
      }
      // Черновики — не отправлены на проверку
      const drafts = this.values.filter(v => v.status === 'draft');
      if (drafts.length > 0) {
        items.push({
          type: 'draft',
          title: `${drafts.length} ${drafts.length === 1 ? 'черновик' : 'черновиков'} не отправлено`,
          description: 'Отправьте на проверку руководителю',
          buttonText: 'Перейти',
          action: () => {
            const el = this.$el.querySelector('.values-section');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          },
        });
      }
      // Пустые группы показателей — нет данных
      const emptyGroups = this.kpiGroups.filter(g => g.score === 0 && g.indicators?.length > 0);
      if (emptyGroups.length > 0) {
        const names = emptyGroups.map(g => g.name).join(', ');
        items.push({
          type: 'empty',
          title: `Нет данных по ${emptyGroups.length} ${emptyGroups.length === 1 ? 'направлению' : 'направлениям'}`,
          description: names,
          buttonText: '+ Добавить',
          action: () => this.showDataInputModal(),
        });
      }
      return items;
    },
    activeRecommendations() {
      return (this.recommendations || []).filter(r => !r.is_completed);
    },
    recHighCount() {
      return this.activeRecommendations.filter(r => r.priority === 'high').length;
    },
    recMediumCount() {
      return this.activeRecommendations.filter(r => r.priority === 'medium').length;
    },
    recLowCount() {
      return this.activeRecommendations.filter(r => r.priority === 'low').length;
    },
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
    },
    diffText() {
      if (this.teamAverage === null) return '';
      const diff = this.totalScore - this.teamAverage;
      if (diff > 0) return `↑ выше команды на ${diff.toFixed(1)}%`;
      if (diff < 0) return `↓ ниже команды на ${Math.abs(diff).toFixed(1)}%`;
      return '= наравне с командой';
    },
    diffClass() {
      if (this.teamAverage === null) return 'neutral';
      const diff = this.totalScore - this.teamAverage;
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
        const response = await kpiAPI.getDashboard(this.selectedPeriod);
        const data = response.data;
        this.totalScore = data.total_score;
        this.totalPoints = data.total_points || 0;
        this.maxPoints = data.max_points || 0;
        this.performanceLevel = data.performance_level;
        this.bonusAmount = data.bonus_amount;
        this.userRole = data.user_role || 'pps';
        this.thresholdWarnings = data.threshold_warnings || [];
        this.kpiGroups = Object.values(data.group_scores);
        this.expandedGroups = Array(this.kpiGroups.length).fill(false);
        await Promise.allSettled([
          this.loadPreviousPeriodData(),
          this.loadRecommendations(),
          this.loadValues(),
          this.loadChartData(),
          this.loadTeamAverage(),
        ]);
      } catch (error) {
        console.error('Ошибка загрузки данных дашборда:', error);
        this.$toast.error('Не удалось загрузить данные дашборда');
      } finally {
        this.dataLoading = false;
      }
    },
    async loadPreviousPeriodData() {
      try {
        const [year, month] = this.selectedPeriod.split('-');
        let prevYear = parseInt(year);
        let prevMonth = parseInt(month) - 1;
        if (prevMonth === 0) { prevMonth = 12; prevYear -= 1; }
        const prevPeriod = `${prevYear}-${String(prevMonth).padStart(2, '0')}`;
        const response = await kpiAPI.getDashboard(prevPeriod);
        this.previousScore = response.data.total_score;
      } catch {
        this.previousScore = 0;
      }
    },
    async loadRecommendations() {
      try {
        const response = await kpiAPI.getRecommendations(this.selectedPeriod);
        this.recommendations = response.data;
      } catch (error) {
        console.error('Ошибка загрузки рекомендаций:', error);
        this.$toast.error('Не удалось загрузить рекомендации');
      }
    },
    async loadValues() {
      this.valuesLoading = true;
      try {
        const response = await kpiAPI.getValuesByParams({ period: this.selectedPeriod });
        this.values = extractResults(response.data);
      } catch (error) {
        console.error('Ошибка загрузки значений KPI:', error);
        this.$toast.error('Не удалось загрузить данные KPI');
        this.values = [];
      } finally {
        this.valuesLoading = false;
      }
    },
    async submitValue(value) {
      try {
        await kpiAPI.submitValue(value.id);
        this.$toast.success('Отправлено на проверку');
        await this.loadValues();
      } catch (error) {
        console.error('Ошибка отправки на проверку:', error);
        this.$toast.error('Не удалось отправить на проверку');
      }
    },
    async loadTeamAverage() {
      try {
        const response = await kpiAPI.getTeamAverage(this.selectedPeriod);
        this.teamAverage = response.data.average_score;
        this.teamUserCount = response.data.user_count;
      } catch {
        this.teamAverage = null;
      }
    },
    canEdit(value) {
      return value && (value.status === 'draft' || value.status === 'rejected');
    },
    canSubmit(value) {
      return value && (value.status === 'draft' || value.status === 'rejected');
    },
    formatStatus(status) {
      const map = { draft: 'Черновик', submitted: 'На проверке', approved: 'Подтверждено', rejected: 'Отклонено' };
      return map[status] || status || '-';
    },
    statusClass(status) {
      return `status-${status}`;
    },
    async loadChartData() {
      try {
        const response = await kpiAPI.getHistory(6);
        if (response.data && Array.isArray(response.data)) {
          const history = response.data.reverse();
          this.chartData = {
            ...this.chartData,
            labels: history.map(item => this.formatDate(item.period)),
            datasets: [{ ...this.chartData.datasets[0], data: history.map(item => item.total_score) }]
          };
        }
      } catch (error) {
        console.error('Ошибка загрузки истории KPI:', error);
      }
    },
    toggleGroup(index) {
      this.expandedGroups[index] = !this.expandedGroups[index];
      this.expandedGroups = [...this.expandedGroups];
    },
    getProgressClass(value) {
      if (value >= 90) return 'excellent';
      if (value >= 70) return 'good';
      if (value >= 50) return 'medium';
      return 'poor';
    },
    formatDate(period) {
      return formatPeriod(period);
    },
    formatCurrency,
    async generateReport() {
      try {
        const response = await kpiAPI.generateReport(this.selectedPeriod);
        downloadPDF(response.data, `KPI_Report_${this.selectedPeriod}.pdf`);
        this.$toast.success('PDF отчёт загружен');
      } catch (error) {
        console.error('Ошибка генерации PDF:', error);
        this.$toast.error('Не удалось сгенерировать PDF');
      }
    },
    async generateExcel() {
      try {
        const response = await kpiAPI.generateExcelReport(this.selectedPeriod);
        downloadPDF(response.data, `KPI_Report_${this.selectedPeriod}.xlsx`);
        this.$toast.success('Excel отчёт загружен');
      } catch (error) {
        console.error('Ошибка генерации Excel:', error);
        this.$toast.error('Не удалось сгенерировать Excel');
      }
    },
    showDataInputModal() {
      this.editingValue = null;
      this.showModal = true;
    },
    openEditModal(value) {
      this.editingValue = value;
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
      this.editingValue = null;
    },
    async openLogs(value) {
      this.showLogsModal = true;
      this.logsLoading = true;
      this.valueLogs = [];
      try {
        const response = await kpiAPI.getValueLogs(value.id);
        this.valueLogs = response.data;
      } catch (error) {
        console.error('Ошибка загрузки истории:', error);
        this.$toast.error('Не удалось загрузить историю');
      } finally {
        this.logsLoading = false;
      }
    },
    formatDateTime(dateStr) {
      const date = new Date(dateStr);
      return date.toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
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

/* Шапка */
.header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; gap: 16px; }
.header-left h1 { margin: 0 0 8px; font-size: 1.5rem; }
.period-selector { display: flex; align-items: center; gap: 8px; }
.period-selector select { padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 0.9rem; }
.header-actions { display: flex; gap: 10px; flex-shrink: 0; padding-top: 4px; }

/* Кнопки — глобальные стили в App.vue */

/* Предупреждения о порогах */
.threshold-warnings { margin-bottom: 16px; }
.threshold-warning {
  background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;
  padding: 10px 16px; margin-bottom: 8px; display: flex; align-items: center;
  gap: 8px; font-size: 0.88rem; color: #856404;
}
.warn-icon { font-size: 1.1rem; }

/* Сводные карточки */
.summary-cards { display: grid; grid-template-columns: 1fr 2fr; gap: 24px; margin-bottom: 28px; }
.card { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); padding: 24px; }
.progress-overview { min-height: 280px; }
.empty-chart { color: #aaa; text-align: center; margin-top: 80px; }
.total-score { text-align: center; }
.score-skeleton { width: 140px; height: 56px; background: #e9ecef; border-radius: 8px; margin: 12px auto; animation: skeleton-pulse 1.4s ease-in-out infinite; }
.skeleton-line { height: 16px; background: #e9ecef; border-radius: 4px; margin: 8px auto; width: 70%; animation: skeleton-pulse 1.4s ease-in-out infinite; }
.skeleton-line.short { width: 45%; }
@keyframes skeleton-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.score-value { font-size: 3.5rem; font-weight: 800; margin: 12px 0; }
.score-value.excellent { color: #28a745; }
.score-value.good { color: #ffc107; }
.score-value.needs-improvement { color: #dc3545; }
.badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; }
.badge.level-высокий { background: #d4edda; color: #155724; }
.badge.level-средний { background: #fff3cd; color: #856404; }
.badge.level-низкий { background: #f8d7da; color: #721c24; }
.badge.warning { background: #fff3cd; color: #856404; }
.points-info { font-size: 1rem; color: #6c757d; margin-bottom: 8px; font-weight: 600; }
.role-badge { background: #e3f2fd; color: #1565c0; margin-left: 8px; }
.bonus-positive { color: #28a745; }
.bonus-negative { color: #dc3545; }
.group-points { font-size: 0.75rem; color: #888; margin-left: 8px; }
.bonus-info { margin-top: 12px; font-size: 0.9rem; color: #555; }
.trend { font-size: 0.85rem; margin-top: 4px; }
.trend.positive { color: #28a745; }
.trend.negative { color: #dc3545; }
.trend.neutral { color: #6c757d; }

/* Сравнение с командой */
.team-compare-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  padding: 20px 28px;
  margin-bottom: 28px;
  display: flex;
  align-items: center;
  gap: 24px;
}
.tc-item { flex: 1; }
.tc-label { display: block; font-size: 0.8rem; color: #888; margin-bottom: 4px; }
.tc-value { font-size: 1.5rem; font-weight: 700; }
.tc-value.excellent { color: #28a745; }
.tc-value.good { color: #ffc107; }
.tc-value.needs-improvement { color: #dc3545; }
.tc-value.neutral { color: #495057; }
.tc-bar-wrap { margin-top: 6px; }
.tc-bar { height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; }
.tc-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.tc-fill.mine { background: #1a73e8; }
.tc-fill.team { background: #6c757d; }
.tc-divider { text-align: center; flex-shrink: 0; }
.tc-diff { font-weight: 600; font-size: 0.9rem; white-space: nowrap; }
.tc-diff.positive { color: #28a745; }
.tc-diff.negative { color: #dc3545; }
.tc-diff.neutral { color: #6c757d; }
.tc-meta { font-size: 0.75rem; color: #aaa; margin-top: 6px; }

/* Мои достижения */
.values-section { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); padding: 24px; margin-bottom: 28px; }
.section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-header h2 { margin: 0; font-size: 1.2rem; }
.period-label { background: #e9ecef; color: #6c757d; font-size: 0.8rem; padding: 3px 10px; border-radius: 12px; }
.values-table-wrap { overflow-x: auto; }
.values-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.values-table th { background: #f8f9fa; padding: 10px 12px; text-align: left; font-weight: 600; color: #495057; border-bottom: 2px solid #dee2e6; white-space: nowrap; }
.values-table td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
.values-table tr:last-child td { border-bottom: none; }
.values-table tr:hover td { background: #fafafa; }
.indicator-cell { display: flex; flex-direction: column; }
.indicator-name { font-weight: 500; }
.indicator-group { font-size: 0.78rem; color: #888; margin-top: 2px; }
.value-cell { font-weight: 600; }
.muted { color: #6c757d; font-weight: 400; }
.comment-cell { color: #6c757d; font-size: 0.85rem; max-width: 200px; }
.action-buttons { display: flex; gap: 6px; flex-wrap: nowrap; }
/* Статус-бейджи — глобальные стили в App.vue */
.values-empty { color: #6c757d; display: flex; align-items: center; padding: 8px 0; }
.values-loading { color: #6c757d; }

/* KPI по группам */
.kpi-groups-section { margin-bottom: 28px; }
.kpi-groups-section h2 { font-size: 1.2rem; margin-bottom: 16px; }
.groups-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.group-card { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); overflow: hidden; border-top: 4px solid #dee2e6; }
.group-card.excellent { border-top-color: #28a745; }
.group-card.good { border-top-color: #ffc107; }
.group-card.medium { border-top-color: #fd7e14; }
.group-card.poor { border-top-color: #dc3545; }
.group-card-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px 8px; cursor: pointer; user-select: none; }
.group-card-header:hover { background: #fafafa; }
.group-card-title { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.95rem; }
.group-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.group-dot.excellent { background: #28a745; }
.group-dot.good { background: #ffc107; }
.group-dot.medium { background: #fd7e14; }
.group-dot.poor { background: #dc3545; }
.group-card-score { display: flex; align-items: center; gap: 8px; }
.score-num { font-weight: 700; font-size: 1.1rem; }
.score-num.excellent { color: #28a745; }
.score-num.good { color: #ffc107; }
.score-num.medium { color: #fd7e14; }
.score-num.poor { color: #dc3545; }
.toggle-btn { font-size: 0.7rem; color: #aaa; }
.group-score-bar { height: 6px; background: #f0f0f0; margin: 0 16px 4px; border-radius: 3px; }
.group-score-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
.group-score-fill.excellent { background: #28a745; }
.group-score-fill.good { background: #ffc107; }
.group-score-fill.medium { background: #fd7e14; }
.group-score-fill.poor { background: #dc3545; }
.group-indicators { padding: 12px 16px 16px; border-top: 1px solid #f0f0f0; display: flex; flex-direction: column; gap: 10px; }
.ind-row { display: flex; flex-direction: column; gap: 4px; }
.ind-name { font-size: 0.85rem; color: #555; }
.ind-bar-wrap { display: flex; align-items: center; gap: 10px; }
.ind-bar { flex: 1; height: 6px; background: #e9ecef; border-radius: 3px; }
.ind-bar-fill { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
.ind-bar-fill.excellent { background: #28a745; }
.ind-bar-fill.good { background: #ffc107; }
.ind-bar-fill.medium { background: #fd7e14; }
.ind-bar-fill.poor { background: #dc3545; }
.ind-values { font-size: 0.78rem; color: #888; white-space: nowrap; }

/* Блок рекомендаций (компактный тизер) */
.rec-summary-block {
  margin-bottom: 28px;
}
.rec-summary-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #f59e0b;
  border-radius: 10px;
  padding: 18px 24px;
  gap: 16px;
}
.rec-summary-left h3 {
  margin: 0 0 8px;
  font-size: 1.05rem;
  color: #92400e;
}
.rec-summary-counts {
  display: flex;
  gap: 10px;
  margin-bottom: 4px;
}
.rec-count {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
}
.rec-count.high { background: #fef2f2; color: #dc2626; }
.rec-count.medium { background: #fffbeb; color: #d97706; }
.rec-count.low { background: #ecfdf5; color: #059669; }
.rec-summary-hint {
  margin: 0;
  font-size: 0.85rem;
  color: #78350f;
}
.btn-rec-link {
  white-space: nowrap;
  text-decoration: none;
  padding: 10px 20px;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-rec-link:hover { background: #d97706; }

/* Блок «Что нужно сделать» */
.action-panel {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  padding: 20px 24px;
  margin-bottom: 24px;
}
.action-panel h3 {
  margin: 0 0 14px;
  font-size: 1.05rem;
  color: #1f2937;
}
.action-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.action-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid transparent;
}
.action-item.rejected {
  background: #fef2f2;
  border-left-color: #dc2626;
}
.action-item.draft {
  background: #fffbeb;
  border-left-color: #f59e0b;
}
.action-item.empty {
  background: #eff6ff;
  border-left-color: #3b82f6;
}
.action-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
}
.action-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.action-text strong {
  font-size: 0.92rem;
  color: #1f2937;
}
.action-text span {
  font-size: 0.82rem;
  color: #6b7280;
}

/* Модалка истории изменений */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}
.logs-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e9ecef;
}
.logs-header h3 { margin: 0; font-size: 1.1rem; }
.close-btn {
  background: none; border: none; font-size: 1.6rem; cursor: pointer;
  color: #aaa; padding: 0; line-height: 1;
}
.close-btn:hover { color: #333; }
.logs-loading, .logs-empty {
  padding: 40px 24px;
  text-align: center;
  color: #6b7280;
}
.logs-timeline {
  padding: 20px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.log-entry {
  display: flex;
  gap: 14px;
  padding: 12px 0;
  border-left: 2px solid #e5e7eb;
  margin-left: 8px;
  padding-left: 20px;
  position: relative;
}
.log-entry:last-child { border-left-color: transparent; }
.log-dot {
  position: absolute;
  left: -7px;
  top: 16px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #d1d5db;
  border: 2px solid white;
}
.log-entry.created .log-dot { background: #3b82f6; }
.log-entry.submitted .log-dot { background: #f59e0b; }
.log-entry.approved .log-dot { background: #10b981; }
.log-entry.rejected .log-dot { background: #ef4444; }
.log-entry.updated .log-dot { background: #8b5cf6; }
.log-content { flex: 1; }
.log-action {
  font-weight: 600;
  font-size: 0.92rem;
  color: #1f2937;
  margin-bottom: 4px;
}
.log-meta {
  display: flex;
  gap: 12px;
  font-size: 0.8rem;
  color: #6b7280;
}
.log-values {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #4b5563;
  background: #f9fafb;
  padding: 4px 10px;
  border-radius: 4px;
  display: inline-block;
}
.log-comment {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #6b7280;
  font-style: italic;
  background: #fef3c7;
  padding: 6px 10px;
  border-radius: 4px;
}
</style>
