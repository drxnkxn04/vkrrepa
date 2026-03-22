<template>
  <div class="crossref-import-container">
    <!-- Заголовок -->
    <div class="import-header">
      <h2>Импорт публикаций из Crossref</h2>
      <p class="subtitle">
        Найдите публикации, выберите нужные и добавьте их в KPI
      </p>
    </div>

    <!-- Вкладки -->
    <div class="import-tabs">
      <button
        :class="['tab-btn', { active: activeTab === 'orcid' }]"
        @click="switchTab('orcid')"
      >
        По ORCID
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'doi' }]"
        @click="switchTab('doi')"
      >
        По DOI
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'search' }]"
        @click="switchTab('search')"
      >
        Поиск
      </button>
    </div>

    <!-- Вкладка: ORCID -->
    <div v-if="activeTab === 'orcid'" class="tab-content">
      <div class="search-row">
        <div class="form-group form-group-grow">
          <label for="orcid-input">ORCID ID</label>
          <input
            type="text"
            id="orcid-input"
            v-model="orcidInput"
            placeholder="0000-0000-0000-0000"
            :disabled="loading"
            @keyup.enter="findByOrcid"
          />
        </div>
        <div class="form-group">
          <label for="year-filter">Год</label>
          <input
            type="number"
            id="year-filter"
            v-model.number="yearFilter"
            :min="1900"
            :max="currentYear"
            placeholder="Все"
            :disabled="loading"
            class="input-year"
          />
        </div>
        <div class="form-group form-group-btn">
          <label>&nbsp;</label>
          <button
            @click="findByOrcid"
            class="btn btn-primary"
            :disabled="loading || !isValidOrcid"
          >
            {{ loading ? 'Поиск...' : 'Найти' }}
          </button>
        </div>
      </div>
      <small class="hint">Формат: 0000-0000-0000-0000. Последний символ может быть X.</small>
    </div>

    <!-- Вкладка: DOI -->
    <div v-if="activeTab === 'doi'" class="tab-content">
      <div class="search-row">
        <div class="form-group form-group-grow">
          <label for="doi-input">DOI</label>
          <input
            type="text"
            id="doi-input"
            v-model="doiInput"
            placeholder="10.1038/nature12345"
            :disabled="loading"
            @keyup.enter="findByDoi"
          />
        </div>
        <div class="form-group form-group-btn">
          <label>&nbsp;</label>
          <button
            @click="findByDoi"
            class="btn btn-primary"
            :disabled="loading || !doiInput.trim()"
          >
            {{ loading ? 'Поиск...' : 'Найти' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Вкладка: Поиск -->
    <div v-if="activeTab === 'search'" class="tab-content">
      <div class="search-row">
        <div class="form-group form-group-grow">
          <label for="search-input">Запрос</label>
          <input
            type="text"
            id="search-input"
            v-model="searchQuery"
            placeholder="Название статьи, автор, ключевые слова..."
            :disabled="loading"
            @keyup.enter="findBySearch"
          />
        </div>
        <div class="form-group form-group-btn">
          <label>&nbsp;</label>
          <button
            @click="findBySearch"
            class="btn btn-primary"
            :disabled="loading || !searchQuery.trim()"
          >
            {{ loading ? 'Поиск...' : 'Найти' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-if="error" class="error-banner">
      <span>{{ error }}</span>
      <button @click="error = null" class="error-close">&times;</button>
    </div>

    <!-- Результаты -->
    <div v-if="publications.length > 0" class="results-section">
      <!-- Панель действий -->
      <div class="results-toolbar">
        <div class="toolbar-left">
          <label class="select-all-label">
            <input
              type="checkbox"
              :checked="allSelected"
              :indeterminate.prop="someSelected && !allSelected"
              @change="toggleSelectAll"
            />
            <span v-if="selectedCount > 0">
              Выбрано: {{ selectedCount }} из {{ publications.length }}
            </span>
            <span v-else>Выбрать все</span>
          </label>
        </div>
        <div class="toolbar-right">
          <button
            @click="addSelectedToKpi"
            class="btn btn-success"
            :disabled="saving || selectedCount === 0"
          >
            {{ saving ? 'Сохранение...' : `Добавить в KPI (${selectedCount})` }}
          </button>
        </div>
      </div>

      <!-- Список публикаций -->
      <div class="pub-list">
        <div
          v-for="pub in publications"
          :key="pub.doi"
          class="pub-card"
          :class="{
            selected: isSelected(pub),
            added: isAdded(pub),
          }"
          @click="toggleSelection(pub)"
        >
          <div class="pub-checkbox">
            <input
              type="checkbox"
              :checked="isSelected(pub)"
              :disabled="isAdded(pub)"
              @click.stop
              @change="toggleSelection(pub)"
            />
          </div>

          <div class="pub-body">
            <div class="pub-title">{{ pub.title }}</div>
            <div class="pub-meta">
              <span v-if="pub.journal" class="meta-tag journal">{{ pub.journal }}</span>
              <span v-if="pub.year" class="meta-tag year">{{ pub.year }}</span>
              <span class="meta-tag type">{{ formatType(pub.type) }}</span>
            </div>
            <div v-if="pub.authors && pub.authors.length" class="pub-authors">
              {{ formatAuthors(pub.authors) }}
            </div>
            <a
              :href="`https://doi.org/${pub.doi}`"
              target="_blank"
              class="pub-doi"
              @click.stop
            >
              DOI: {{ pub.doi }}
            </a>
          </div>

          <div v-if="isAdded(pub)" class="pub-badge added-badge">
            Добавлено
          </div>
        </div>
      </div>

      <!-- Нижняя панель -->
      <div v-if="selectedCount > 0 && !allAdded" class="results-footer">
        <button
          @click="addSelectedToKpi"
          class="btn btn-success btn-lg"
          :disabled="saving"
        >
          {{ saving ? 'Сохранение...' : `Добавить выбранные в KPI (${selectedCount})` }}
        </button>
      </div>
    </div>

    <!-- Пустой результат -->
    <div v-if="!loading && publications.length === 0 && hasSearched" class="empty-state">
      <p>Публикации не найдены</p>
      <small>Попробуйте изменить параметры поиска</small>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading-bar">
      <div class="loading-spinner"></div>
      <span>{{ loadingMessage }}</span>
    </div>
  </div>
</template>

<script>
import { kpiAPI } from '@/services/api';

export default {
  name: 'CrossrefImport',
  emits: ['publications-added'],
  data() {
    return {
      activeTab: 'orcid',
      orcidInput: '',
      doiInput: '',
      searchQuery: '',
      yearFilter: null,
      publications: [],
      selectedDois: new Set(),
      addedDois: new Set(),
      loading: false,
      saving: false,
      error: null,
      hasSearched: false,
      loadingMessage: '',
      currentYear: new Date().getFullYear(),
    };
  },
  computed: {
    isValidOrcid() {
      return /^\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$/.test(this.orcidInput);
    },
    selectedCount() {
      // Only count non-added publications
      return [...this.selectedDois].filter(doi => !this.addedDois.has(doi)).length;
    },
    allSelected() {
      const selectable = this.publications.filter(p => !this.addedDois.has(p.doi));
      return selectable.length > 0 && selectable.every(p => this.selectedDois.has(p.doi));
    },
    someSelected() {
      return this.selectedCount > 0;
    },
    allAdded() {
      return this.publications.length > 0 && this.publications.every(p => this.addedDois.has(p.doi));
    },
  },
  methods: {
    switchTab(tab) {
      this.activeTab = tab;
      this.error = null;
    },

    clearResults() {
      this.publications = [];
      this.selectedDois = new Set();
      this.hasSearched = false;
      this.error = null;
    },

    // --- Search methods ---

    async findByOrcid() {
      if (!this.isValidOrcid) return;

      this.clearResults();
      this.loading = true;
      this.loadingMessage = 'Поиск публикаций в Crossref...';

      try {
        const response = await kpiAPI.syncCrossref({
          orcid: this.orcidInput.toUpperCase(),
          year: this.yearFilter,
          save_to_kpi: false,
        });

        this.hasSearched = true;

        if (response.data.success) {
          this.publications = response.data.publications || [];
          if (this.publications.length === 0) {
            this.$toast.info('Публикации не найдены');
          }
        } else {
          this.error = response.data.error || 'Ошибка при поиске';
        }
      } catch (err) {
        this.hasSearched = true;
        this.error = this.parseError(err);
      } finally {
        this.loading = false;
      }
    },

    async findByDoi() {
      if (!this.doiInput.trim()) return;

      this.clearResults();
      this.loading = true;
      this.loadingMessage = 'Поиск по DOI...';

      try {
        const response = await kpiAPI.searchByDoi(this.doiInput.trim());
        this.hasSearched = true;

        if (response.data) {
          this.publications = [response.data];
        }
      } catch (err) {
        this.hasSearched = true;
        if (err.response?.status === 404) {
          this.error = 'Публикация с таким DOI не найдена';
        } else {
          this.error = this.parseError(err);
        }
      } finally {
        this.loading = false;
      }
    },

    async findBySearch() {
      if (!this.searchQuery.trim()) return;

      this.clearResults();
      this.loading = true;
      this.loadingMessage = 'Поиск публикаций...';

      try {
        const response = await kpiAPI.searchCrossref(this.searchQuery.trim());
        this.hasSearched = true;
        this.publications = response.data.publications || [];

        if (this.publications.length === 0) {
          this.$toast.info('Публикации не найдены');
        }
      } catch (err) {
        this.hasSearched = true;
        this.error = this.parseError(err);
      } finally {
        this.loading = false;
      }
    },

    // --- Selection ---

    isSelected(pub) {
      return this.selectedDois.has(pub.doi);
    },

    isAdded(pub) {
      return this.addedDois.has(pub.doi);
    },

    toggleSelection(pub) {
      if (this.addedDois.has(pub.doi)) return;

      const next = new Set(this.selectedDois);
      if (next.has(pub.doi)) {
        next.delete(pub.doi);
      } else {
        next.add(pub.doi);
      }
      this.selectedDois = next;
    },

    toggleSelectAll() {
      const selectable = this.publications.filter(p => !this.addedDois.has(p.doi));
      const next = new Set(this.selectedDois);

      if (this.allSelected) {
        selectable.forEach(p => next.delete(p.doi));
      } else {
        selectable.forEach(p => next.add(p.doi));
      }
      this.selectedDois = next;
    },

    // --- Save to KPI ---

    async addSelectedToKpi() {
      const doisToSave = [...this.selectedDois].filter(doi => !this.addedDois.has(doi));
      if (doisToSave.length === 0) return;

      const pubsToSave = this.publications.filter(p => doisToSave.includes(p.doi));

      this.saving = true;
      this.error = null;

      try {
        let response;

        if (this.activeTab === 'orcid') {
          // For ORCID: use sync endpoint with selected_dois filter
          response = await kpiAPI.syncCrossref({
            orcid: this.orcidInput.toUpperCase(),
            year: this.yearFilter,
            save_to_kpi: true,
            selected_dois: doisToSave,
          });
        } else {
          // For DOI/Search: pass publication data directly
          response = await kpiAPI.savePublicationsToKpi(pubsToSave);
        }

        const data = response.data;
        const saved = data.saved_to_kpi || 0;
        const skipped = data.skipped || 0;
        const errors = data.errors || [];

        // Mark as added
        doisToSave.forEach(doi => this.addedDois.add(doi));
        // Clear selection
        this.selectedDois = new Set();

        // Show result
        const parts = [];
        if (saved > 0) parts.push(`Добавлено: ${saved}`);
        if (skipped > 0) parts.push(`Уже были: ${skipped}`);
        if (errors.length > 0) parts.push(`Ошибок: ${errors.length}`);
        const msg = parts.join(', ') || 'Нет новых публикаций для добавления';

        if (saved > 0) {
          this.$toast.success(msg);
          this.$emit('publications-added', saved);
        } else if (errors.length > 0) {
          this.$toast.warning(msg);
        } else {
          this.$toast.info(msg);
        }
      } catch (err) {
        this.error = this.parseError(err);
      } finally {
        this.saving = false;
      }
    },

    // --- Helpers ---

    parseError(err) {
      if (err.response?.status === 429) return 'Превышен лимит запросов. Попробуйте через пару минут.';
      if (err.response?.status === 503) return 'Crossref API временно недоступен.';
      if (err.response?.status === 504) return 'Таймаут запроса. Попробуйте указать конкретный год.';
      return err.response?.data?.error || 'Произошла ошибка. Попробуйте ещё раз.';
    },

    formatType(type) {
      const map = {
        'journal-article': 'Журнал',
        'proceedings-article': 'Конференция',
        'posted-content': 'Препринт',
        'book-chapter': 'Глава книги',
      };
      return map[type] || type || '—';
    },

    formatAuthors(authors) {
      if (!authors || authors.length === 0) return '';
      if (authors.length <= 3) return authors.join(', ');
      return `${authors.slice(0, 3).join(', ')} и др.`;
    },
  },
};
</script>

<style scoped>
.crossref-import-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.import-header {
  margin-bottom: 24px;
}

.import-header h2 {
  margin: 0 0 4px 0;
  color: #2c3e50;
  font-size: 1.4rem;
}

.subtitle {
  margin: 0;
  color: #7f8c8d;
}

/* Tabs */
.import-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 2px solid #e9ecef;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.95rem;
  color: #7f8c8d;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  transition: color 0.15s;
}

.tab-btn:hover { color: #3498db; }
.tab-btn.active {
  color: #3498db;
  border-bottom-color: #3498db;
}

/* Tab content */
.tab-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  margin-bottom: 16px;
}

.search-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group-grow { flex: 1; }

.form-group label {
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  color: #2c3e50;
}

.form-group input {
  padding: 9px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.15s;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.input-year { width: 100px; }

.hint {
  display: block;
  margin-top: 8px;
  color: #95a5a6;
  font-size: 0.82rem;
}

/* Error */
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin-bottom: 16px;
  color: #b91c1c;
  font-size: 0.9rem;
}

.error-close {
  background: none;
  border: none;
  font-size: 1.3rem;
  cursor: pointer;
  color: #b91c1c;
  padding: 0 4px;
}

/* Results */
.results-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  overflow: hidden;
}

.results-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.select-all-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  color: #495057;
  user-select: none;
}

.select-all-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

/* Publication list */
.pub-list {
  padding: 8px;
}

.pub-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s;
  border: 1px solid transparent;
}

.pub-card:hover {
  background: #f8f9fa;
}

.pub-card.selected {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.pub-card.added {
  opacity: 0.6;
  cursor: default;
}

.pub-checkbox {
  padding-top: 2px;
}

.pub-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.pub-body {
  flex: 1;
  min-width: 0;
}

.pub-title {
  font-weight: 600;
  color: #1a202c;
  line-height: 1.4;
  margin-bottom: 8px;
}

.pub-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}

.meta-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.meta-tag.journal {
  background: #e8f4fd;
  color: #1a73e8;
}

.meta-tag.year {
  background: #fef3c7;
  color: #92400e;
}

.meta-tag.type {
  background: #f3e8ff;
  color: #7c3aed;
}

.pub-authors {
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 4px;
}

.pub-doi {
  font-size: 0.82rem;
  color: #3498db;
  text-decoration: none;
}

.pub-doi:hover { text-decoration: underline; }

.pub-badge {
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
  align-self: center;
}

.added-badge {
  background: #d1fae5;
  color: #065f46;
}

/* Footer */
.results-footer {
  padding: 16px 20px;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
}

/* Empty & loading */
.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: #9ca3af;
}

.empty-state p { margin: 0 0 4px; font-size: 1.05rem; }

.loading-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  color: #6b7280;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Buttons */
.btn {
  padding: 9px 18px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.15s;
  white-space: nowrap;
}

.btn:hover:not(:disabled) { filter: brightness(0.95); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary { background: #3498db; color: white; }
.btn-success { background: #10b981; color: white; }

.btn-lg {
  padding: 12px 28px;
  font-size: 1rem;
}

/* Responsive */
@media (max-width: 640px) {
  .search-row {
    flex-direction: column;
  }

  .input-year { width: 100%; }

  .form-group-btn { align-self: stretch; }
  .form-group-btn .btn { width: 100%; }

  .results-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .toolbar-right .btn { width: 100%; }
}
</style>
