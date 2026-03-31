<template>
  <div class="pending-card">
    <div class="pending-header">
      <h2>На проверке</h2>
      <span v-if="values.length > 0" class="pending-count">{{ values.length }} записей</span>
    </div>

    <!-- Панель массового действия -->
    <transition name="bulk-bar">
      <div v-if="selectedIds.length > 0" class="bulk-action-bar">
        <span class="bulk-count">Выбрано: <b>{{ selectedIds.length }}</b></span>
        <input
          class="bulk-comment-input"
          type="text"
          v-model="bulkComment"
          placeholder="Комментарий для всех (необязательно)"
        />
        <button class="btn btn-sm btn-approve" @click="$emit('bulk-approve', { ids: selectedIds, comment: bulkComment })">
          Подтвердить ({{ selectedIds.length }})
        </button>
        <button class="btn btn-sm btn-reject" @click="$emit('bulk-reject', { ids: selectedIds, comment: bulkComment })">
          Отклонить ({{ selectedIds.length }})
        </button>
        <button class="btn btn-sm btn-outline-cancel" @click="selectedIds = []">Отмена</button>
      </div>
    </transition>

    <div v-if="loading" class="pending-loading">Загрузка...</div>
    <div v-else-if="values.length > 0" class="table-responsive">
      <table class="pending-table">
        <thead>
          <tr>
            <th class="cb-col">
              <input
                type="checkbox"
                :checked="selectedIds.length === values.length && values.length > 0"
                :indeterminate.prop="selectedIds.length > 0 && selectedIds.length < values.length"
                @change="toggleSelectAll"
              />
            </th>
            <th>Сотрудник</th>
            <th>Показатель</th>
            <th>Период</th>
            <th>Факт</th>
            <th>План</th>
            <th>Документ</th>
            <th>Комментарий сотрудника</th>
            <th>Комментарий проверки</th>
            <th>Решение</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="value in values"
            :key="value.id"
            :class="{ 'row-selected': selectedIds.includes(value.id) }"
          >
            <td class="cb-col">
              <input type="checkbox" :value="value.id" v-model="selectedIds" />
            </td>
            <td>{{ value.user?.full_name || value.user?.username || '—' }}</td>
            <td>{{ value.indicator?.name || '—' }}</td>
            <td>{{ formatPeriod(value.period) }}</td>
            <td>{{ value.actual_value }}</td>
            <td>{{ value.target_value }}</td>
            <td>
              <a v-if="value.evidence" :href="value.evidence" target="_blank" class="evidence-link" title="Открыть документ">
                Открыть
              </a>
              <span v-else class="no-evidence">—</span>
            </td>
            <td class="employee-comment">{{ value.comment || '—' }}</td>
            <td>
              <input
                class="review-input"
                type="text"
                v-model="reviewComments[value.id]"
                placeholder="Комментарий..."
              />
            </td>
            <td>
              <button class="btn btn-sm btn-approve" @click="$emit('approve', { value, comment: reviewComments[value.id] || '' })">✓</button>
              <button class="btn btn-sm btn-reject" @click="$emit('reject', { value, comment: reviewComments[value.id] || '' })">✗</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="pending-empty">Нет записей на проверке</div>
  </div>
</template>

<script>
import { formatPeriod } from '@/utils/formatters';

export default {
  name: 'PendingValuesTable',
  props: {
    values: { type: Array, required: true },
    loading: { type: Boolean, default: false },
  },
  emits: ['approve', 'reject', 'bulk-approve', 'bulk-reject'],
  data() {
    return {
      selectedIds: [],
      bulkComment: '',
      reviewComments: {},
    };
  },
  watch: {
    values() {
      this.selectedIds = [];
      this.bulkComment = '';
      this.reviewComments = {};
    },
  },
  methods: {
    formatPeriod,
    toggleSelectAll(e) {
      this.selectedIds = e.target.checked ? this.values.map(v => v.id) : [];
    },
    clearSelection() {
      this.selectedIds = [];
      this.bulkComment = '';
    },
  },
};
</script>

<style scoped>
.pending-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.pending-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.pending-header h2 { margin: 0; color: #2c3e50; }

.pending-count {
  background: #e9ecef;
  color: #495057;
  font-size: 0.8rem;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 600;
}

.bulk-action-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f0f7ff;
  border: 1.5px solid #1a73e8;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.bulk-count { font-weight: 600; font-size: 0.9rem; color: #1a73e8; white-space: nowrap; }

.bulk-comment-input {
  flex: 1;
  min-width: 180px;
  padding: 6px 10px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 0.88rem;
}

.btn-outline-cancel { background: white; border: 1px solid #dee2e6; color: #6c757d; cursor: pointer; padding: 5px 12px; border-radius: 4px; }
.btn-outline-cancel:hover { background: #f8f9fa; }

.bulk-bar-enter-active, .bulk-bar-leave-active { transition: all 0.2s ease; }
.bulk-bar-enter-from, .bulk-bar-leave-to { opacity: 0; transform: translateY(-8px); }

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
}

.pending-table tr:hover { background: #f8f9fa; }

.cb-col { width: 36px; text-align: center; }
.row-selected td { background: #f0f7ff !important; }

.pending-loading, .pending-empty {
  color: #6c757d;
  text-align: center;
  padding: 20px;
}

.review-input {
  width: 100%;
  min-width: 140px;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.evidence-link {
  color: #007bff;
  text-decoration: none;
  font-size: 0.85rem;
  white-space: nowrap;
}
.evidence-link:hover { text-decoration: underline; }
.no-evidence { color: #aaa; }
.employee-comment { color: #555; font-size: 0.85rem; max-width: 160px; }

.btn-approve { margin-right: 6px; }
</style>
