<template>
  <div v-if="visible" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="modal-header">
        <h3>{{ user?.full_name || user?.username || 'Сотрудник' }}</h3>
        <button class="close-button" @click="$emit('close')" title="Закрыть">&times;</button>
      </div>

      <!-- Сводка по сотруднику -->
      <div v-if="user" class="user-summary">
        <div class="summary-item">
          <span class="summary-label">Балл KPI</span>
          <span class="summary-value" :class="getScoreClass(user.total_score)">
            {{ user.total_score?.toFixed(1) }}%
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Уровень</span>
          <span class="level-badge" :class="'level-' + user.performance_level">
            {{ formatLevel(user.performance_level) }}
          </span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Бонус</span>
          <span class="summary-value">{{ formatCurrency(user.bonus_amount) }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Роль</span>
          <span class="role-tag" :class="user.user_role || 'pps'">
            {{ user.user_role === 'rop' ? 'РОП' : 'ППС' }}
          </span>
        </div>
      </div>

      <div v-if="loading" class="pending-loading">Загрузка...</div>
      <div v-else-if="values.length === 0" class="pending-empty">
        Нет данных за выбранный период.
      </div>
      <div v-else class="table-responsive">
        <table class="pending-table detail-table">
          <thead>
            <tr>
              <th>Показатель</th>
              <th>Факт / План</th>
              <th>Выполнение</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="value in values" :key="value.id">
              <td>
                <div class="detail-indicator">
                  <span class="detail-ind-name">{{ value.indicator?.name || '-' }}</span>
                  <span class="detail-ind-group">{{ value.indicator?.group?.name || '' }}</span>
                </div>
              </td>
              <td class="detail-values">
                <strong>{{ value.actual_value }}</strong>
                <span class="detail-separator">/</span>
                <span class="detail-target">{{ value.target_value }}</span>
              </td>
              <td>
                <div class="detail-progress">
                  <div class="detail-bar">
                    <div
                      class="detail-bar-fill"
                      :class="getScoreClass(calcPercent(value))"
                      :style="{ width: Math.min(calcPercent(value), 100) + '%' }"
                    ></div>
                  </div>
                  <span class="detail-percent">{{ calcPercent(value).toFixed(0) }}%</span>
                </div>
              </td>
              <td>
                <span class="status-badge" :class="'status-' + value.status">
                  {{ formatStatusText(value.status) }}
                </span>
              </td>
              <td>
                <button class="btn btn-sm btn-outline" @click="$emit('open-logs', value)">
                  Лог
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { formatCurrency, getScoreClass } from '@/utils/formatters';

export default {
  name: 'UserDetailsModal',
  props: {
    visible: { type: Boolean, default: false },
    user: { type: Object, default: null },
    values: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
  },
  emits: ['close', 'open-logs'],
  methods: {
    formatCurrency,
    getScoreClass,
    formatLevel(level) {
      const levels = { 'высокий': 'Высокая', 'средний': 'Средняя', 'низкий': 'Низкая' };
      return levels[level] || level;
    },
    calcPercent(value) {
      if (!value.target_value || value.target_value === 0) return 0;
      return (value.actual_value / value.target_value) * 100;
    },
    formatStatusText(status) {
      const map = { draft: 'Черновик', submitted: 'На проверке', approved: 'Подтверждено', rejected: 'Отклонено' };
      return map[status] || status || '-';
    },
  },
};
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 1000;
}

.modal-card {
  width: min(900px, 100%);
  max-height: 85vh;
  overflow: auto;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.modal-header h3 { margin: 0; font-size: 1.15rem; }

.close-button {
  background: none;
  border: none;
  font-size: 1.6rem;
  cursor: pointer;
  color: #aaa;
  padding: 0;
  line-height: 1;
}
.close-button:hover { color: #333; }

.user-summary {
  display: flex;
  gap: 24px;
  padding: 14px 20px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-value { font-weight: 700; font-size: 1.1rem; }
.summary-value.excellent { color: #16a34a; }
.summary-value.good { color: #ca8a04; }
.summary-value.medium { color: #ea580c; }
.summary-value.poor { color: #dc2626; }

.role-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 0.82rem;
  font-weight: 600;
}
.role-tag.pps { background: #e8f4fd; color: #1a73e8; }
.role-tag.rop { background: #fef3e2; color: #e67700; }

.level-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
}
.level-badge.level-высокий { background: #d4edda; color: #155724; }
.level-badge.level-средний { background: #fff3cd; color: #856404; }
.level-badge.level-низкий { background: #f8d7da; color: #721c24; }

.pending-loading, .pending-empty {
  color: #6c757d;
  text-align: center;
  padding: 20px;
}

.table-responsive { overflow-x: auto; }

.pending-table {
  width: 100%;
  border-collapse: collapse;
}

.pending-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #e9ecef;
}

.pending-table td {
  padding: 12px;
  border-bottom: 1px solid #e9ecef;
  vertical-align: middle;
}

.pending-table tr:hover { background: #f8f9fa; }

.detail-indicator { display: flex; flex-direction: column; }
.detail-ind-name { font-weight: 500; font-size: 0.9rem; }
.detail-ind-group { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }
.detail-values { white-space: nowrap; }
.detail-values strong { font-size: 0.95rem; }
.detail-separator { color: #d1d5db; margin: 0 4px; }
.detail-target { color: #6b7280; }

.detail-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.detail-bar {
  flex: 1;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.detail-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s;
}
.detail-bar-fill.excellent { background: #16a34a; }
.detail-bar-fill.good { background: #ca8a04; }
.detail-bar-fill.medium { background: #ea580c; }
.detail-bar-fill.poor { background: #dc2626; }

.detail-percent {
  font-size: 0.82rem;
  font-weight: 600;
  color: #374151;
  min-width: 36px;
  text-align: right;
}

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 0.82rem;
  font-weight: 500;
}
.status-badge.status-draft { background: #e9ecef; color: #495057; }
.status-badge.status-submitted { background: #fff3cd; color: #856404; }
.status-badge.status-approved { background: #d4edda; color: #155724; }
.status-badge.status-rejected { background: #f8d7da; color: #721c24; }
</style>
