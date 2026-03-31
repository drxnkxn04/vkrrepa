<template>
  <div class="users-table-card">
    <h2>Рейтинг сотрудников</h2>
    <div class="table-responsive">
      <table class="users-table">
        <thead>
          <tr>
            <th class="rank-col">#</th>
            <th>Сотрудник</th>
            <th>Роль</th>
            <th class="score-col">Балл KPI</th>
            <th>Баллы</th>
            <th>Уровень</th>
            <th class="bonus-col">Бонус</th>
            <th class="actions-col">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(user, index) in users" :key="user.user_id">
            <td class="rank-col">
              <span class="rank-badge" :class="getRankClass(index)">
                {{ index + 1 }}
              </span>
            </td>
            <td class="user-col">
              <div class="user-info">
                <div class="user-avatar">
                  {{ getInitials(user.full_name) }}
                </div>
                <div>
                  <strong>{{ user.full_name }}</strong>
                  <small>@{{ user.username }}</small>
                </div>
              </div>
            </td>
            <td>
              <span class="role-tag" :class="user.user_role || 'pps'">
                {{ user.user_role === 'rop' ? 'РОП' : 'ППС' }}
              </span>
            </td>
            <td class="score-col">
              <div class="score-wrapper">
                <div class="score-bar">
                  <div
                    class="score-fill"
                    :style="{ width: user.total_score + '%' }"
                    :class="getScoreClass(user.total_score)"
                  ></div>
                </div>
                <span class="score-text">{{ user.total_score.toFixed(1) }}%</span>
              </div>
            </td>
            <td class="points-col">
              <span v-if="user.max_points">{{ (user.total_points || 0).toFixed(0) }}/{{ (user.max_points || 0).toFixed(0) }}</span>
              <span v-else>—</span>
            </td>
            <td>
              <span class="level-badge" :class="'level-' + user.performance_level">
                {{ formatLevel(user.performance_level) }}
              </span>
            </td>
            <td class="bonus-col">
              <strong>{{ formatCurrency(user.bonus_amount) }}</strong>
            </td>
            <td class="actions-col">
              <button
                @click="$emit('view-details', user.user_id)"
                class="btn-icon"
                title="Просмотр деталей"
              >
                Просмотр
              </button>
              <button
                @click="$emit('download-pdf', user.user_id)"
                class="btn-icon"
                title="Скачать PDF отчёт"
              >
                PDF
              </button>
              <button
                @click="$emit('download-excel', user.user_id)"
                class="btn-icon"
                title="Скачать Excel отчёт"
              >
                Excel
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { formatCurrency, getScoreClass } from '@/utils/formatters';

export default {
  name: 'UsersTable',
  props: {
    users: { type: Array, required: true },
  },
  emits: ['view-details', 'download-pdf', 'download-excel'],
  methods: {
    formatCurrency,
    getScoreClass,
    formatLevel(level) {
      const levels = { 'высокий': 'Высокая', 'средний': 'Средняя', 'низкий': 'Низкая' };
      return levels[level] || level;
    },
    getRankClass(index) {
      if (index === 0) return 'gold';
      if (index === 1) return 'silver';
      if (index === 2) return 'bronze';
      return '';
    },
    getInitials(fullName) {
      return (fullName || 'User').split(' ').map(w => w[0] || '').join('').toUpperCase().slice(0, 2);
    },
  },
};
</script>
