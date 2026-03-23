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
        <button @click="exportData" class="btn btn-secondary">
          📊 Экспорт
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
          <div class="card-icon">👥</div>
          <div class="card-content">
            <h3>Всего сотрудников</h3>
            <p class="card-value">{{ users.length }}</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-icon">⭐</div>
          <div class="card-content">
            <h3>Средний балл</h3>
            <p class="card-value">{{ averageScore.toFixed(1) }}%</p>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-icon">🏆</div>
          <div class="card-content">
            <h3>Высокая эффективность</h3>
            <p class="card-value">{{ highPerformers }}</p>
            <span class="card-subtitle">{{ highPerformersPercent }}%</span>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-icon">💰</div>
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
            placeholder="🔍 Поиск по имени или email..."
            @input="filterUsers"
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
      <div class="users-table-card">
        <h2>📊 Рейтинг сотрудников</h2>
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
              <tr v-for="(user, index) in filteredUsers" :key="user.user_id">
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
                    @click="viewUserDetails(user.user_id)" 
                    class="btn-icon"
                    title="Просмотр деталей"
                  >
                    👁️
                  </button>
                  <button
                    @click="generateUserReport(user.user_id)"
                    class="btn-icon"
                    title="Скачать PDF отчёт"
                  >
                    📄
                  </button>
                  <button
                    @click="generateUserExcelReport(user.user_id)"
                    class="btn-icon"
                    title="Скачать Excel отчёт"
                  >
                    📊
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Блок на проверке -->
      <div class="pending-card">
        <div class="pending-header">
          <h2>✋ На проверке</h2>
          <span v-if="pendingValues.length > 0" class="pending-count">{{ pendingValues.length }} записей</span>
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
            <button class="btn btn-sm btn-approve" @click="bulkApprove">
              ✓ Подтвердить ({{ selectedIds.length }})
            </button>
            <button class="btn btn-sm btn-reject" @click="bulkReject">
              ✗ Отклонить ({{ selectedIds.length }})
            </button>
            <button class="btn btn-sm btn-outline-cancel" @click="selectedIds = []">Отмена</button>
          </div>
        </transition>

        <div v-if="pendingLoading" class="pending-loading">Загрузка...</div>
        <div v-else-if="pendingValues.length > 0" class="table-responsive">
          <table class="pending-table">
            <thead>
              <tr>
                <th class="cb-col">
                  <input
                    type="checkbox"
                    :checked="selectedIds.length === pendingValues.length && pendingValues.length > 0"
                    :indeterminate.prop="selectedIds.length > 0 && selectedIds.length < pendingValues.length"
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
                v-for="value in pendingValues"
                :key="value.id"
                :class="{ 'row-selected': selectedIds.includes(value.id) }"
              >
                <td class="cb-col">
                  <input
                    type="checkbox"
                    :value="value.id"
                    v-model="selectedIds"
                  />
                </td>
                <td>{{ value.user?.full_name || value.user?.username || '—' }}</td>
                <td>{{ value.indicator?.name || '—' }}</td>
                <td>{{ formatPeriod(value.period) }}</td>
                <td>{{ value.actual_value }}</td>
                <td>{{ value.target_value }}</td>
                <td>
                  <a
                    v-if="value.evidence"
                    :href="value.evidence"
                    target="_blank"
                    class="evidence-link"
                    title="Открыть документ"
                  >
                    📎 Открыть
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
                  <button class="btn btn-sm btn-approve" @click="approveValue(value)">✓</button>
                  <button class="btn btn-sm btn-reject" @click="rejectValue(value)">✗</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="pending-empty">✅ Нет записей на проверке</div>
      </div>

      <!-- Диаграмма распределения -->
      <div class="distribution-card">
        <h2>📈 Распределение по уровням эффективности</h2>
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
      <div class="empty-icon">📊</div>
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
          🔄 Обновить список периодов
        </button>
      </div>
    </div>

    <div v-if="showUserDetails" class="modal-backdrop" @click.self="closeUserDetails">
      <div class="modal-card">
        <div class="modal-header">
          <h3>
            Детали KPI:
            {{ selectedUser?.full_name || selectedUser?.username || 'Сотрудник' }}
          </h3>
          <button class="btn-icon" @click="closeUserDetails" title="Закрыть">x</button>
        </div>

        <div v-if="userDetailsLoading" class="pending-loading">Загрузка...</div>
        <div v-else-if="selectedUserValues.length === 0" class="pending-empty">
          Нет данных за выбранный период.
        </div>
        <div v-else class="table-responsive">
          <table class="pending-table">
            <thead>
              <tr>
                <th>Показатель</th>
                <th>Период</th>
                <th>Факт</th>
                <th>План</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="value in selectedUserValues" :key="value.id">
                <td>{{ value.indicator?.name || '-' }}</td>
                <td>{{ value.period }}</td>
                <td>{{ value.actual_value }}</td>
                <td>{{ value.target_value }}</td>
                <td>{{ value.status || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { kpiAPI, downloadPDF, extractResults } from '@/services/api';

export default {
  name: 'ManagerDashboardView',
  data() {
    return {
      selectedPeriod: '',
      availablePeriods: [],
      users: [],
      filteredUsers: [],
      loading: false,
      searchQuery: '',
      selectedFilter: 'all',
      sortBy: 'score-desc',
      pendingValues: [],
      pendingLoading: false,
      reviewComments: {},
      selectedIds: [],
      bulkComment: '',
      showUserDetails: false,
      selectedUser: null,
      selectedUserValues: [],
      userDetailsLoading: false
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
    await this.loadPeriods();
  },
  methods: {
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
        const response = await kpiAPI.getManagerDashboard(this.selectedPeriod);
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
    toggleSelectAll(e) {
      if (e.target.checked) {
        this.selectedIds = this.pendingValues.map(v => v.id);
      } else {
        this.selectedIds = [];
      }
    },
    async bulkApprove() {
      if (!this.selectedIds.length) return;
      try {
        const res = await kpiAPI.bulkApprove(this.selectedIds, this.bulkComment);
        this.$toast.success(`Подтверждено: ${res.data.approved}`);
        this.selectedIds = [];
        this.bulkComment = '';
        await this.loadData();
      } catch (error) {
        console.error('Ошибка массового подтверждения:', error);
        this.$toast.error('Не удалось подтвердить');
      }
    },
    async bulkReject() {
      if (!this.selectedIds.length) return;
      try {
        const res = await kpiAPI.bulkReject(this.selectedIds, this.bulkComment);
        this.$toast.success(`Отклонено: ${res.data.rejected}`);
        this.selectedIds = [];
        this.bulkComment = '';
        await this.loadData();
      } catch (error) {
        console.error('Ошибка массового отклонения:', error);
        this.$toast.error('Не удалось отклонить');
      }
    },
    async approveValue(value) {
      try {
        const comment = this.reviewComments[value.id] || '';
        await kpiAPI.approveValue(value.id, comment);
        this.$toast.success('Запись подтверждена');
        await this.loadData();
      } catch (error) {
        console.error('Ошибка подтверждения:', error);
        this.$toast.error('Не удалось подтвердить');
      }
    },
    async rejectValue(value) {
      try {
        const comment = this.reviewComments[value.id] || '';
        if (!comment) {
          this.$toast.warning('Укажите причину отклонения');
          return;
        }
        await kpiAPI.rejectValue(value.id, comment);
        this.$toast.success('Запись отклонена');
        await this.loadData();
      } catch (error) {
        console.error('Ошибка отклонения:', error);
        this.$toast.error('Не удалось отклонить');
      }
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
    formatPeriod(period) {
      if (!period) return '—';
      const [year, month] = period.split('-');
      const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                          'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
      return `${monthNames[parseInt(month) - 1]} ${year}`;
    },
    formatCurrency(amount) {
      return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
      }).format(amount);
    },
    formatLevel(level) {
      const levels = {
        'высокий': 'Высокая',
        'средний': 'Средняя',
        'низкий': 'Низкая'
      };
      return levels[level] || level;
    },
    getScoreClass(score) {
      if (score >= 90) return 'excellent';
      if (score >= 70) return 'good';
      if (score >= 50) return 'medium';
      return 'poor';
    },
    getRankClass(index) {
      if (index === 0) return 'gold';
      if (index === 1) return 'silver';
      if (index === 2) return 'bronze';
      return '';
    },
    getInitials(fullName) {
      return (fullName || 'User')
        .split(' ')
        .map(word => word[0] || '')
        .join('')
        .toUpperCase()
        .slice(0, 2);
    },
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
    }
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

/* Buttons */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: opacity 0.2s;
}

.btn:hover {
  opacity: 0.9;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-sm {
  padding: 6px 10px;
  font-size: 0.85rem;
}

.btn-approve {
  background: #27ae60;
  color: #fff;
  margin-right: 6px;
}

.btn-reject {
  background: #e74c3c;
  color: #fff;
}

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
</style>






