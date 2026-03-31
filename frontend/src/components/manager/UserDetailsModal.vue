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
