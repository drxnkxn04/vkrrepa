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
