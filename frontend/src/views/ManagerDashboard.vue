<template>
  <div class="manager-container">
    <div class="page-header">
      <h1> Дашборд руководителя</h1>
      <div class="controls">
        <label for="period">Период:</label>
        <select id="period" v-model="selectedPeriod" @change="loadData">
          <option v-for="period in availablePeriods" :key="period" :value="period">
            {{ formatPeriod(period) }}
          </option>
        </select>
        <div class="role-tabs">
          <button
            :class="['role-tab', { active: roleFilter === 'pps' }]"
            @click="setRoleFilter('pps')"
          >ППС</button>
          <button
            :class="['role-tab', { active: roleFilter === 'rop' }]"
            @click="setRoleFilter('rop')"
          >РОП</button>
          <button
            :class="['role-tab', { active: roleFilter === 'all' }]"
            @click="setRoleFilter('all')"
          >Все</button>
        </div>
        <button @click="exportData" class="btn btn-secondary">
          Экспорт CSV
        </button>
        <button @click="downloadSummaryPdf" class="btn btn-secondary">
          Сводный PDF
        </button>
        <button @click="downloadSummaryExcel" class="btn btn-secondary">
          Сводный Excel
        </button>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Загрузка данных...</p>
    </div>

    <!-- Основной контент -->
    <div v-else-if="users.length > 0">
      <!-- Общая статистика -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-content">
            <h3>Всего сотрудников</h3>
            <p class="card-value">{{ users.length }}</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-content">
            <h3>Средний балл</h3>
            <p class="card-value">{{ averageScore.toFixed(1) }}%</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-content">
            <h3>Высокая эффективность</h3>
            <p class="card-value">{{ highPerformers }}</p>
            <span class="card-subtitle">{{ highPerformersPercent }}%</span>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-content">
            <h3>Общий фонд премий</h3>
            <p class="card-value">{{ formatCurrency(totalBonus) }}</p>
          </div>
        </div>
      </div>

      <!-- Фильтры и поиск -->
      <div class="filters-section">
        <div class="search-box">
          <input
            type="text"
            v-model="searchQuery"
            placeholder="Поиск по имени или email..."
            @input="debouncedFilterUsers"
          />
        </div>
        <div class="filter-buttons">
          <button 
            :class="['filter-btn', { active: selectedFilter === 'all' }]"
            @click="setFilter('all')"
          >
            Все ({{ users.length }})
          </button>
          <button 
            :class="['filter-btn', { active: selectedFilter === 'high' }]"
            @click="setFilter('high')"
          >
            Высокие ({{ highPerformers }})
          </button>
          <button 
            :class="['filter-btn', { active: selectedFilter === 'medium' }]"
            @click="setFilter('medium')"
          >
            Средние ({{ mediumPerformers }})
          </button>
          <button 
            :class="['filter-btn', { active: selectedFilter === 'low' }]"
            @click="setFilter('low')"
          >
            Низкие ({{ lowPerformers }})
          </button>
        </div>
        <div class="sort-controls">
          <label>Сортировка:</label>
          <select v-model="sortBy" @change="sortUsers">
            <option value="score-desc">Балл (убыв.)</option>
            <option value="score-asc">Балл (возр.)</option>
            <option value="name-asc">Имя (А-Я)</option>
            <option value="name-desc">Имя (Я-А)</option>
            <option value="bonus-desc">Премия (убыв.)</option>
          </select>
        </div>
      </div>

      <!-- Таблица сотрудников -->
      <div class="section-header">
        <h2>Рейтинг сотрудников</h2>
        <button @click="openTargetsModal" class="btn btn-primary btn-sm">
          Назначить планы
        </button>
      </div>
      <users-table
        :users="filteredUsers"
        @view-details="viewUserDetails"
        @download-pdf="generateUserReport"
        @download-excel="generateUserExcelReport"
      />

      <!-- Блок на проверке -->
      <pending-values-table
        ref="pendingTable"
        :values="pendingValues"
        :loading="pendingLoading"
        @approve="onApproveValue"
        @reject="onRejectValue"
        @bulk-approve="onBulkApprove"
        @bulk-reject="onBulkReject"
      />

      <!-- Диаграмма распределения -->
      <div class="distribution-card">
        <h2>Распределение по уровням эффективности</h2>
        <div class="distribution-chart">
          <div class="distribution-bar">
            <div 
              class="distribution-segment high"
              :style="{ width: highPerformersPercent + '%' }"
            >
              <span v-if="highPerformersPercent > 10">{{ highPerformers }}</span>
            </div>
            <div 
              class="distribution-segment medium"
              :style="{ width: mediumPerformersPercent + '%' }"
            >
              <span v-if="mediumPerformersPercent > 10">{{ mediumPerformers }}</span>
            </div>
            <div 
              class="distribution-segment low"
              :style="{ width: lowPerformersPercent + '%' }"
            >
              <span v-if="lowPerformersPercent > 10">{{ lowPerformers }}</span>
            </div>
          </div>
          <div class="distribution-legend">
            <div class="legend-item">
              <span class="legend-color high"></span>
              <span>Высокая ({{ highPerformers }} чел.)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color medium"></span>
              <span>Средняя ({{ mediumPerformers }} чел.)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color low"></span>
              <span>Низкая ({{ lowPerformers }} чел.)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Пустое состояние -->
    <div v-else class="empty-state">
      <div class="empty-icon"></div>
      <h2>Нет данных</h2>
      <p>Не найдено сотрудников за выбранный период</p>
      <div class="empty-hint">
        <p><strong>Возможные причины:</strong></p>
        <ul>
          <li>Сотрудники еще не внесли данные за этот период</li>
          <li>Выбран период без данных</li>
          <li>Данные не прошли проверку</li>
        </ul>
        <button @click="loadPeriods" class="btn btn-primary">
          Обновить список периодов
        </button>
      </div>
    </div>

    <user-details-modal
      :visible="showUserDetails"
      :user="selectedUser"
      :values="selectedUserValues"
      :loading="userDetailsLoading"
      @close="closeUserDetails"
      @open-logs="openValueLogs"
    />

    <!-- Модалка истории изменений -->
    <div v-if="showLogsModal" class="modal-backdrop logs-backdrop" @click.self="showLogsModal = false">
      <div class="logs-modal">
        <div class="logs-modal-header">
          <h3>История изменений</h3>
          <button class="btn-icon" @click="showLogsModal = false">x</button>
        </div>
        <div v-if="logsLoading" class="pending-loading">Загрузка...</div>
        <div v-else-if="valueLogs.length === 0" class="pending-empty">Нет записей</div>
        <div v-else class="logs-timeline">
          <div
            v-for="log in valueLogs"
            :key="log.id"
            class="log-entry"
            :class="log.action"
          >
            <div class="log-dot"></div>
            <div class="log-body">
              <div class="log-action-text">{{ log.action_display }}</div>
              <div class="log-meta">
                <span>{{ log.actor_name || 'Система' }}</span>
                <span>{{ formatLogDate(log.created_at) }}</span>
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

    <!-- Модалка индивидуальных планов -->
    <div v-if="showTargetsModal" class="modal-backdrop" @click.self="showTargetsModal = false">
      <div class="modal-card targets-modal">
        <div class="modal-header">
          <h3>Индивидуальные планы на {{ formatPeriod(selectedPeriod) }}</h3>
          <button class="close-button" @click="showTargetsModal = false">&times;</button>
        </div>

        <div class="targets-controls">
          <label>Сотрудник:</label>
          <select v-model="targetUserId" @change="loadTargetsForUser">
            <option disabled value="">Выберите сотрудника</option>
            <option v-for="u in users" :key="u.user_id" :value="u.user_id">
              {{ u.full_name }}
            </option>
          </select>
        </div>

        <div v-if="targetUserId && targetIndicators.length > 0" class="targets-table-wrap">
          <table class="pending-table">
            <thead>
              <tr>
                <th>Показатель</th>
                <th>План по умолчанию</th>
                <th>Индивидуальный план</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ind in targetIndicators" :key="ind.id">
                <td>
                  <div class="detail-indicator">
                    <span class="detail-ind-name">{{ ind.name }}</span>
                    <span class="detail-ind-group">{{ ind.group_name }}</span>
                  </div>
                </td>
                <td class="text-center">{{ ind.default_target }}</td>
                <td>
                  <input
                    type="number"
                    class="review-input"
                    v-model.number="ind.custom_target"
                    step="any"
                    min="0"
                    :placeholder="String(ind.default_target)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
          <div class="targets-actions">
            <button class="btn btn-primary" @click="saveTargets" :disabled="targetsSaving">
              {{ targetsSaving ? 'Сохранение...' : 'Сохранить планы' }}
            </button>
          </div>
        </div>
        <div v-else-if="targetUserId" class="pending-loading">Загрузка показателей...</div>
        <div v-else class="pending-empty">Выберите сотрудника</div>
      </div>
    </div>

    <confirm-dialog
      :visible="confirmDialog.visible"
      :title="confirmDialog.title"
      :message="confirmDialog.message"
      :confirm-text="confirmDialog.confirmText"
      :danger="confirmDialog.danger"
      @confirm="onConfirm"
      @cancel="confirmDialog.visible = false"
    />
  </div>
</template>

<script>
import { kpiAPI, downloadPDF, extractResults } from '@/services/api';
import { getScoreClass } from '@/utils/formatters';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
import UsersTable from '@/components/manager/UsersTable.vue';
import PendingValuesTable from '@/components/manager/PendingValuesTable.vue';
import UserDetailsModal from '@/components/manager/UserDetailsModal.vue';
import { formatPeriod, formatCurrency } from '@/utils/formatters';

export default {
  name: 'ManagerDashboardView',
  components: { ConfirmDialog, UsersTable, PendingValuesTable, UserDetailsModal },
  data() {
    return {
      selectedPeriod: '',
      availablePeriods: [],
      roleFilter: 'pps',
      users: [],
      filteredUsers: [],
      loading: false,
      searchQuery: '',
      selectedFilter: 'all',
      sortBy: 'score-desc',
      pendingValues: [],
      pendingLoading: false,
      showUserDetails: false,
      selectedUser: null,
      selectedUserValues: [],
      userDetailsLoading: false,
      showLogsModal: false,
      valueLogs: [],
      logsLoading: false,
      confirmDialog: {
        visible: false,
        title: '',
        message: '',
        confirmText: 'Подтвердить',
        danger: false,
        action: null,
      },
      // Индивидуальные планы
      showTargetsModal: false,
      targetUserId: '',
      targetIndicators: [],
      targetsSaving: false,
    };
  },
  computed: {
    averageScore() {
      if (this.users.length === 0) return 0;
      const sum = this.users.reduce((acc, user) => acc + user.total_score, 0);
      return sum / this.users.length;
    },
    highPerformers() {
      return this.users.filter(u => u.performance_level === 'высокий').length;
    },
    mediumPerformers() {
      return this.users.filter(u => u.performance_level === 'средний').length;
    },
    lowPerformers() {
      return this.users.filter(u => u.performance_level === 'низкий').length;
    },
    highPerformersPercent() {
      return this.users.length ? (this.highPerformers / this.users.length * 100).toFixed(1) : 0;
    },
    mediumPerformersPercent() {
      return this.users.length ? (this.mediumPerformers / this.users.length * 100).toFixed(1) : 0;
    },
    lowPerformersPercent() {
      return this.users.length ? (this.lowPerformers / this.users.length * 100).toFixed(1) : 0;
    },
    totalBonus() {
      return this.users.reduce((acc, user) => acc + user.bonus_amount, 0);
    }
  },
  async created() {
    this._filterTimeout = null;
    await this.loadPeriods();
  },
  beforeUnmount() {
    clearTimeout(this._filterTimeout);
  },
  methods: {
    debouncedFilterUsers() {
      clearTimeout(this._filterTimeout);
      this._filterTimeout = setTimeout(() => this.filterUsers(), 250);
    },
    async loadPeriods() {
      try {
        // Получаем все уникальные периоды из системы
        const response = await kpiAPI.getPeriods();
        this.availablePeriods = response.data;
        
        if (this.availablePeriods.length > 0) {
          // Выбираем последний период (самый свежий)
          this.selectedPeriod = this.availablePeriods[0];
          await this.loadData();
        } else {
          // Если периодов нет, используем текущий месяц
          const now = new Date();
          this.selectedPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
          this.availablePeriods = [this.selectedPeriod];
          await this.loadData();
        }
      } catch (error) {
        console.error('Ошибка загрузки периодов:', error);
        this.$toast.error('Не удалось загрузить список периодов');
        
        // Fallback: используем текущий месяц
        const now = new Date();
        this.selectedPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
        this.availablePeriods = [this.selectedPeriod];
      }
    },
    async loadData() {
      this.loading = true;
      try {
        const response = await kpiAPI.getManagerDashboard(this.selectedPeriod, this.roleFilter);
        this.users = response.data.users || [];
        this.filteredUsers = [...this.users];
        this.sortUsers();
        await this.loadPending();
        
        if (this.users.length === 0) {
          this.$toast.info(`Нет данных за период ${this.formatPeriod(this.selectedPeriod)}`);
        }
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        this.$toast.error('Не удалось загрузить данные дашборда');
        this.users = [];
        this.filteredUsers = [];
      } finally {
        this.loading = false;
      }
    },
    filterUsers() {
      let result = [...this.users];

      // Фильтр по уровню
      if (this.selectedFilter !== 'all') {
        const levelMap = {
          'high': 'высокий',
          'medium': 'средний',
          'low': 'низкий'
        };
        result = result.filter(u => u.performance_level === levelMap[this.selectedFilter]);
      }

      // Поиск
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(u => 
          (u.full_name || '').toLowerCase().includes(query) ||
          (u.username || '').toLowerCase().includes(query) ||
          (u.email || '').toLowerCase().includes(query)
        );
      }

      this.filteredUsers = result;
      this.sortUsers();
    },
    setFilter(filter) {
      this.selectedFilter = filter;
      this.filterUsers();
    },
    async setRoleFilter(role) {
      this.roleFilter = role;
      await this.loadData();
    },
    async loadPending() {
      this.pendingLoading = true;
      try {
        const response = await kpiAPI.getPendingValues(this.selectedPeriod);
        this.pendingValues = extractResults(response.data);
      } catch (error) {
        console.error('Ошибка загрузки на проверке:', error);
        this.pendingValues = [];
      } finally {
        this.pendingLoading = false;
      }
    },
    async onApproveValue({ value, comment }) {
      try {
        await kpiAPI.approveValue(value.id, comment);
        this.$toast.success('Запись подтверждена');
        await this.loadData();
      } catch (error) {
        console.error('Ошибка подтверждения:', error);
        this.$toast.error('Не удалось подтвердить');
      }
    },
    onRejectValue({ value, comment }) {
      if (!comment) {
        this.$toast.warning('Укажите причину отклонения');
        return;
      }
      const employeeName = value.user?.full_name || value.user?.username || 'сотрудника';
      const indicatorName = value.indicator?.name || 'показатель';
      this.showConfirm({
        title: 'Отклонение записи',
        message: `Отклонить "${indicatorName}" для ${employeeName}?`,
        confirmText: 'Отклонить',
        danger: true,
        action: async () => {
          try {
            await kpiAPI.rejectValue(value.id, comment);
            this.$toast.success('Запись отклонена');
            await this.loadData();
          } catch (error) {
            console.error('Ошибка отклонения:', error);
            this.$toast.error('Не удалось отклонить');
          }
        },
      });
    },
    async onBulkApprove({ ids, comment }) {
      try {
        const res = await kpiAPI.bulkApprove(ids, comment);
        this.$toast.success(`Подтверждено: ${res.data.approved}`);
        this.$refs.pendingTable?.clearSelection();
        await this.loadData();
      } catch (error) {
        console.error('Ошибка массового подтверждения:', error);
        this.$toast.error('Не удалось подтвердить');
      }
    },
    onBulkReject({ ids, comment }) {
      const count = ids.length;
      this.showConfirm({
        title: 'Массовое отклонение',
        message: `Вы уверены, что хотите отклонить ${count} ${count === 1 ? 'запись' : 'записей'}?`,
        confirmText: 'Отклонить',
        danger: true,
        action: async () => {
          try {
            const res = await kpiAPI.bulkReject(ids, comment);
            this.$toast.success(`Отклонено: ${res.data.rejected}`);
            this.$refs.pendingTable?.clearSelection();
            await this.loadData();
          } catch (error) {
            console.error('Ошибка массового отклонения:', error);
            this.$toast.error('Не удалось отклонить');
          }
        },
      });
    },
    sortUsers() {
      const [field, order] = this.sortBy.split('-');
      
      this.filteredUsers.sort((a, b) => {
        let compareValue = 0;
        
        switch(field) {
          case 'score':
            compareValue = a.total_score - b.total_score;
            break;
          case 'name':
            compareValue = a.full_name.localeCompare(b.full_name);
            break;
          case 'bonus':
            compareValue = a.bonus_amount - b.bonus_amount;
            break;
        }
        
        return order === 'desc' ? -compareValue : compareValue;
      });
    },
    formatPeriod,
    formatCurrency,
    async viewUserDetails(userId) {
      this.showUserDetails = true;
      this.userDetailsLoading = true;
      this.selectedUserValues = [];
      this.selectedUser = this.users.find(u => u.user_id === userId) || null;

      try {
        const response = await kpiAPI.getValuesByParams({
          scope: 'all',
          user_id: userId,
          period: this.selectedPeriod,
        });
        this.selectedUserValues = extractResults(response.data);
      } catch (error) {
        console.error('Failed to load user details:', error);
        this.$toast.error('Не удалось загрузить детали');
      } finally {
        this.userDetailsLoading = false;
      }
    },
    async generateUserReport(userId) {
      try {
        const response = await kpiAPI.generateUserReport(userId, this.selectedPeriod);
        const target = this.users.find(u => u.user_id === userId);
        const username = target?.username || `user_${userId}`;
        downloadPDF(response.data, `KPI_Report_${username}_${this.selectedPeriod}.pdf`);
        this.$toast.success('Отчет сгенерирован');
      } catch (error) {
        console.error('Report generation error:', error);
        this.$toast.error('Ошибка генерации отчета');
      }
    },
    async generateUserExcelReport(userId) {
      try {
        const response = await kpiAPI.generateUserExcelReport(userId, this.selectedPeriod);
        const target = this.users.find(u => u.user_id === userId);
        const username = target?.username || `user_${userId}`;
        downloadPDF(response.data, `KPI_Report_${username}_${this.selectedPeriod}.xlsx`);
        this.$toast.success('Excel отчёт загружен');
      } catch (error) {
        console.error('Excel report error:', error);
        this.$toast.error('Ошибка генерации Excel отчёта');
      }
    },
    exportData() {
      if (!this.filteredUsers.length) {
        this.$toast.warning('Нет данных для экспорта');
        return;
      }

      const rows = [
        ['Rank', 'Full Name', 'Username', 'Email', 'Score', 'Level', 'Bonus'],
        ...this.filteredUsers.map((u, index) => [
          index + 1,
          u.full_name || '',
          u.username || '',
          u.email || '',
          Number(u.total_score || 0).toFixed(1),
          u.performance_level || '',
          Number(u.bonus_amount || 0).toFixed(0),
        ]),
      ];

      const csv = rows
        .map(row => row.map(value => this.escapeCsv(value)).join(','))
        .join('\n');
      const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `manager_kpi_${this.selectedPeriod}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      this.$toast.success('Экспорт выполнен');
    },
    escapeCsv(value) {
      const str = String(value ?? '');
      return `"${str.replace(/"/g, '""')}"`;
    },
    closeUserDetails() {
      this.showUserDetails = false;
      this.selectedUser = null;
      this.selectedUserValues = [];
    },
    async openValueLogs(value) {
      this.showLogsModal = true;
      this.logsLoading = true;
      this.valueLogs = [];
      try {
        const response = await kpiAPI.getValueLogs(value.id);
        this.valueLogs = response.data;
      } catch (error) {
        console.error('Ошибка загрузки логов:', error);
        this.$toast.error('Не удалось загрузить историю');
      } finally {
        this.logsLoading = false;
      }
    },
    formatLogDate(dateStr) {
      const date = new Date(dateStr);
      return date.toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    },
    showConfirm({ title, message, confirmText, danger, action }) {
      this.confirmDialog = { visible: true, title, message, confirmText, danger, action };
    },
    async onConfirm() {
      if (this.confirmDialog.action) {
        await this.confirmDialog.action();
      }
      this.confirmDialog.visible = false;
    },

    // === Сводные отчёты ===
    async downloadSummaryPdf() {
      try {
        const response = await kpiAPI.generateSummaryReport(this.selectedPeriod, this.roleFilter);
        downloadPDF(response.data, `KPI_Summary_${this.selectedPeriod}.pdf`);
        this.$toast.success('Сводный PDF-отчёт сгенерирован');
      } catch (error) {
        console.error('Summary PDF error:', error);
        this.$toast.error('Ошибка генерации сводного PDF');
      }
    },
    async downloadSummaryExcel() {
      try {
        const response = await kpiAPI.generateSummaryExcel(this.selectedPeriod, this.roleFilter);
        downloadPDF(response.data, `KPI_Summary_${this.selectedPeriod}.xlsx`);
        this.$toast.success('Сводный Excel-отчёт загружен');
      } catch (error) {
        console.error('Summary Excel error:', error);
        this.$toast.error('Ошибка генерации сводного Excel');
      }
    },

    // === Индивидуальные планы ===
    openTargetsModal() {
      this.showTargetsModal = true;
      this.targetUserId = '';
      this.targetIndicators = [];
    },
    async loadTargetsForUser() {
      if (!this.targetUserId) return;
      this.targetIndicators = [];

      try {
        // Загружаем группы и показатели
        const groupsRes = await kpiAPI.getGroups();
        const groups = Array.isArray(groupsRes.data) ? groupsRes.data : groupsRes.data.results || [];

        // Загружаем существующие планы
        const targetsRes = await kpiAPI.getTargets(this.selectedPeriod, this.targetUserId);
        const existingTargets = extractResults(targetsRes.data);
        const targetsMap = {};
        for (const t of existingTargets) {
          targetsMap[t.indicator?.id] = t;
        }

        // Формируем список показателей
        const indicators = [];
        for (const group of groups) {
          for (const ind of (group.indicators || [])) {
            const existing = targetsMap[ind.id];
            indicators.push({
              id: ind.id,
              name: ind.name,
              group_name: group.name,
              default_target: ind.max_value || 0,
              custom_target: existing ? existing.target_value : null,
              existing_id: existing ? existing.id : null,
            });
          }
        }
        this.targetIndicators = indicators;
      } catch (error) {
        console.error('Error loading targets:', error);
        this.$toast.error('Не удалось загрузить показатели');
      }
    },
    async saveTargets() {
      this.targetsSaving = true;
      try {
        const targets = this.targetIndicators
          .filter(ind => ind.custom_target !== null && ind.custom_target !== '' && ind.custom_target !== ind.default_target)
          .map(ind => ({
            user_id: this.targetUserId,
            indicator_id: ind.id,
            period: this.selectedPeriod,
            target_value: ind.custom_target,
          }));

        if (targets.length === 0) {
          this.$toast.info('Нет изменений для сохранения');
          this.targetsSaving = false;
          return;
        }

        const res = await kpiAPI.bulkSetTargets(targets);
        this.$toast.success(`Планы сохранены: создано ${res.data.created}, обновлено ${res.data.updated}`);
        this.showTargetsModal = false;
        await this.loadData();
      } catch (error) {
        console.error('Error saving targets:', error);
        this.$toast.error('Ошибка сохранения планов');
      } finally {
        this.targetsSaving = false;
      }
    },
  }
};
</script>

<style scoped>
.manager-container {
  max-width: 1600px;
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

.controls select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.role-tabs {
  display: flex;
  border: 1.5px solid #dee2e6;
  border-radius: 6px;
  overflow: hidden;
}

.role-tab {
  padding: 7px 16px;
  border: none;
  background: white;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 500;
  color: #555;
  transition: all 0.2s;
  border-right: 1px solid #dee2e6;
}

.role-tab:last-child {
  border-right: none;
}

.role-tab:hover {
  background: #f0f7ff;
}

.role-tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.summary-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon {
  font-size: 2.5rem;
}

.card-content h3 {
  margin: 0 0 8px 0;
  font-size: 0.9rem;
  color: #7f8c8d;
  font-weight: 500;
}

.card-value {
  margin: 0;
  font-size: 1.8rem;
  font-weight: bold;
  color: #2c3e50;
}

.card-subtitle {
  font-size: 0.85rem;
  color: #95a5a6;
}

/* Filters */
.filters-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.search-box {
  flex: 1;
  min-width: 250px;
}

.search-box input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.filter-buttons {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.filter-btn:hover {
  background: #f8f9fa;
}

.filter-btn.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-controls select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

/* Table */
.users-table-card, .pending-card, .distribution-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.users-table-card h2, .pending-card h2, .distribution-card h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
}

.table-responsive {
  overflow-x: auto;
}

.users-table, .pending-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th, .pending-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #e9ecef;
}

.users-table td, .pending-table td {
  padding: 12px;
  border-bottom: 1px solid #e9ecef;
}

.users-table tr:hover, .pending-table tr:hover {
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

.rank-badge.gold {
  background: #ffd700;
  color: #fff;
}

.rank-badge.silver {
  background: #c0c0c0;
  color: #fff;
}

.rank-badge.bronze {
  background: #cd7f32;
  color: #fff;
}

.user-col {
  min-width: 200px;
}

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

.score-col {
  min-width: 150px;
}

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

.bonus-col {
  text-align: right;
}

.actions-col {
  width: 100px;
  text-align: center;
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

/* Pending */
.pending-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.pending-header h2 { margin: 0; }
.pending-count { background: #e9ecef; color: #495057; font-size: 0.8rem; padding: 3px 10px; border-radius: 12px; font-weight: 600; }

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
.btn-outline-cancel { background: white; border: 1px solid #dee2e6; color: #6c757d; }
.btn-outline-cancel:hover { background: #f8f9fa; }

.bulk-bar-enter-active, .bulk-bar-leave-active { transition: all 0.2s ease; }
.bulk-bar-enter-from, .bulk-bar-leave-to { opacity: 0; transform: translateY(-8px); }

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

/* Distribution Chart */
.distribution-bar {
  display: flex;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.distribution-segment {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1.2rem;
  transition: all 0.3s ease;
}

.distribution-segment.high { background: #27ae60; }
.distribution-segment.medium { background: #f39c12; }
.distribution-segment.low { background: #e74c3c; }

.distribution-legend {
  display: flex;
  justify-content: center;
  gap: 32px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-color.high { background: #27ae60; }
.legend-color.medium { background: #f39c12; }
.legend-color.low { background: #e74c3c; }

/* Loading & Empty States */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
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

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-hint {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
  max-width: 500px;
}

.empty-hint ul {
  text-align: left;
  margin: 12px 0;
}

/* Кнопки — глобальные стили в App.vue */
.btn-approve { margin-right: 6px; }

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
  background: none; border: none; font-size: 1.6rem; cursor: pointer;
  color: #aaa; padding: 0; line-height: 1;
}
.close-button:hover { color: #333; }

/* Сводка по сотруднику */
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
.summary-value {
  font-weight: 700;
  font-size: 1.1rem;
}
.summary-value.excellent { color: #16a34a; }
.summary-value.good { color: #ca8a04; }
.summary-value.medium { color: #ea580c; }
.summary-value.poor { color: #dc2626; }

/* Таблица деталей */
.detail-table td { vertical-align: middle; }
.detail-indicator { display: flex; flex-direction: column; }
.detail-ind-name { font-weight: 500; font-size: 0.9rem; }
.detail-ind-group { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }
.detail-values { white-space: nowrap; }
.detail-values strong { font-size: 0.95rem; }
.detail-separator { color: #d1d5db; margin: 0 4px; }
.detail-target { color: #6b7280; }
.detail-progress { display: flex; align-items: center; gap: 8px; min-width: 120px; }
.detail-bar { flex: 1; height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
.detail-bar-fill { height: 100%; border-radius: 3px; transition: width 0.4s; }
.detail-bar-fill.excellent { background: #16a34a; }
.detail-bar-fill.good { background: #ca8a04; }
.detail-bar-fill.medium { background: #ea580c; }
.detail-bar-fill.poor { background: #dc2626; }
.detail-percent { font-size: 0.82rem; font-weight: 600; color: #374151; min-width: 36px; text-align: right; }

/* Лог-модалка */
.logs-backdrop { z-index: 2000; }
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
.logs-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e9ecef;
}
.logs-modal-header h3 { margin: 0; font-size: 1.1rem; }
.logs-timeline {
  padding: 20px 24px;
  overflow-y: auto;
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
.log-body { flex: 1; }
.log-action-text { font-weight: 600; font-size: 0.92rem; color: #1f2937; margin-bottom: 4px; }
.log-meta { display: flex; gap: 12px; font-size: 0.8rem; color: #6b7280; }
.log-values {
  margin-top: 6px; font-size: 0.85rem; color: #4b5563;
  background: #f9fafb; padding: 4px 10px; border-radius: 4px; display: inline-block;
}
.log-comment {
  margin-top: 6px; font-size: 0.85rem; color: #6b7280;
  font-style: italic; background: #fef3c7; padding: 6px 10px; border-radius: 4px;
}

/* Section header */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.section-header h2 {
  margin: 0;
  color: #2c3e50;
}

/* Targets modal */
.targets-modal {
  width: min(1000px, 95%);
}
.targets-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px 16px;
}
.targets-controls select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.92rem;
}
.targets-controls label {
  font-weight: 600;
  font-size: 0.88rem;
  color: #444;
  white-space: nowrap;
}
.targets-table-wrap {
  padding: 0 20px 20px;
  max-height: 50vh;
  overflow-y: auto;
}
.targets-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}
.text-center { text-align: center; }
</style>






