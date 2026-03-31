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

<style scoped>
.users-table-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.users-table-card h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
}

.table-responsive {
  overflow-x: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #e9ecef;
}

.users-table td {
  padding: 12px;
  border-bottom: 1px solid #e9ecef;
}

.users-table tr:hover {
  background: #f8f9fa;
}

.rank-col {
  width: 60px;
  text-align: center;
}

.rank-badge {
  display: inline-block;
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 50%;
  background: #e9ecef;
  font-weight: 600;
  color: #2c3e50;
}

.rank-badge.gold { background: #ffd700; color: #fff; }
.rank-badge.silver { background: #c0c0c0; color: #fff; }
.rank-badge.bronze { background: #cd7f32; color: #fff; }

.user-col { min-width: 200px; }

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #3498db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.user-info small {
  display: block;
  color: #95a5a6;
  font-size: 0.85rem;
}

.role-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 0.82rem;
  font-weight: 600;
}

.role-tag.pps { background: #e8f4fd; color: #1a73e8; }
.role-tag.rop { background: #fef3e2; color: #e67700; }

.score-col { min-width: 150px; }

.score-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.score-fill.excellent { background: #27ae60; }
.score-fill.good { background: #f39c12; }
.score-fill.medium { background: #e67e22; }
.score-fill.poor { background: #e74c3c; }

.score-text {
  font-weight: 600;
  white-space: nowrap;
}

.points-col { white-space: nowrap; }

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

.bonus-col { text-align: right; }

.actions-col {
  width: 100px;
  text-align: center;
}

.btn-icon {
  background: none;
  border: 1px solid #dee2e6;
  cursor: pointer;
  font-size: 0.82rem;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  margin: 0 2px;
}

.btn-icon:hover {
  background: #f0f7ff;
  border-color: #1a73e8;
  color: #1a73e8;
}
</style>
