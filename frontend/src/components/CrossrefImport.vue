<template>
  <div class="crossref-import-container">
    <!-- Заголовок -->
    <div class="import-header">
      <h2>🔄 Импорт публикаций из Crossref</h2>
      <p class="subtitle">
        Автоматически загрузите ваши научные публикации по ORCID ID или DOI
      </p>
    </div>

    <!-- Вкладки выбора метода импорта -->
    <div class="import-tabs">
      <button 
        :class="['tab-button', { active: activeTab === 'orcid' }]"
        @click="activeTab = 'orcid'"
      >
        📋 По ORCID
      </button>
      <button 
        :class="['tab-button', { active: activeTab === 'doi' }]"
        @click="activeTab = 'doi'"
      >
        🔗 По DOI
      </button>
      <button 
        :class="['tab-button', { active: activeTab === 'search' }]"
        @click="activeTab = 'search'"
      >
        🔍 Поиск
      </button>
    </div>

    <!-- Вкладка: Импорт по ORCID -->
    <div v-if="activeTab === 'orcid'" class="tab-content">
      <div class="form-group">
        <label for="orcid-input">ORCID ID</label>
        <input 
          type="text" 
          id="orcid-input"
          v-model="orcidInput"
          placeholder="0000-0000-0000-0000"
          pattern="\d{4}-\d{4}-\d{4}-\d{3}[\dX]"
          :disabled="loading"
        />
        <small>Формат: 0000-0000-0000-0000</small>
      </div>

      <div class="form-group">
        <label for="year-filter">Год публикации (необязательно)</label>
        <input 
          type="number" 
          id="year-filter"
          v-model.number="yearFilter"
          :min="1900"
          :max="currentYear"
          placeholder="Например: 2024"
          :disabled="loading"
        />
      </div>

      <button 
        @click="importByOrcid" 
        class="btn btn-primary btn-import"
        :disabled="loading || !isValidOrcid"
      >
        <span v-if="!loading">🚀 Импортировать публикации</span>
        <span v-else>⏳ Загрузка...</span>
      </button>
    </div>

    <!-- Вкладка: Импорт по DOI -->
    <div v-if="activeTab === 'doi'" class="tab-content">
      <div class="form-group">
        <label for="doi-input">DOI публикации</label>
        <input 
          type="text" 
          id="doi-input"
          v-model="doiInput"
          placeholder="10.1000/xyz123"
          :disabled="loading"
        />
        <small>Например: 10.1038/nature12345</small>
      </div>

      <button 
        @click="importByDoi" 
        class="btn btn-primary btn-import"
        :disabled="loading || !doiInput"
      >
        <span v-if="!loading">🔍 Найти публикацию</span>
        <span v-else>⏳ Поиск...</span>
      </button>
    </div>

    <!-- Вкладка: Поиск -->
    <div v-if="activeTab === 'search'" class="tab-content">
      <div class="form-group">
        <label for="search-input">Поисковый запрос</label>
        <input 
          type="text" 
          id="search-input"
          v-model="searchQuery"
          placeholder="Название статьи, автор, ключевые слова..."
          :disabled="loading"
          @keyup.enter="searchPublications"
        />
      </div>

      <button 
        @click="searchPublications" 
        class="btn btn-primary btn-import"
        :disabled="loading || !searchQuery"
      >
        <span v-if="!loading">🔍 Поиск</span>
        <span v-else>⏳ Поиск...</span>
      </button>
    </div>

    <!-- Ошибки -->
    <div v-if="error" class="error-block">
      <div class="error-icon">❌</div>
      <div class="error-content">
        <h4>Произошла ошибка</h4>
        <p>{{ error }}</p>
        <button @click="error = null" class="btn-dismiss">Закрыть</button>
      </div>
    </div>

    <!-- Результаты импорта -->
    <div v-if="publications.length > 0" class="results-section">
      <div class="results-header">
        <h3>📚 Найдено публикаций: {{ publications.length }}</h3>
        <div class="results-actions">
          <button @click="selectAll" class="btn btn-sm btn-outline">
            {{ allSelected ? 'Снять все' : 'Выбрать все' }}
          </button>
          <button 
            @click="addSelectedPublications" 
            class="btn btn-sm btn-success"
            :disabled="selectedPublications.length === 0 || adding"
          >
            {{ adding ? 'Добавление...' : `Добавить выбранные (${selectedPublications.length})` }}
          </button>
        </div>
      </div>

      <!-- Список публикаций -->
      <div class="publications-list">
        <div 
          v-for="(pub, index) in publications" 
          :key="pub.doi"
          class="publication-card"
          :class="{ selected: isSelected(pub) }"
        >
          <!-- Чекбокс выбора -->
          <div class="publication-select">
            <input 
              type="checkbox" 
              :id="`pub-${index}`"
              :checked="isSelected(pub)"
              @change="toggleSelection(pub)"
            />
          </div>

          <!-- Контент публикации -->
          <div class="publication-content">
            <h4 class="publication-title">{{ pub.title }}</h4>
            
            <div class="publication-meta">
              <span class="meta-item">
                <strong>Журнал:</strong> {{ pub.journal || 'Не указан' }}
              </span>
              <span class="meta-item">
                <strong>Год:</strong> {{ pub.year || 'Не указан' }}
              </span>
              <span class="meta-item">
                <strong>Тип:</strong> {{ formatPublicationType(pub.type) }}
              </span>
            </div>

            <div v-if="pub.authors && pub.authors.length > 0" class="publication-authors">
              <strong>Авторы:</strong> {{ formatAuthors(pub.authors) }}
            </div>

            <div class="publication-links">
              <a :href="pub.url" target="_blank" class="link-doi">
                🔗 DOI: {{ pub.doi }}
              </a>
            </div>
          </div>

          <!-- Статус добавления -->
          <div v-if="addedPublications.includes(pub.doi)" class="publication-status">
            <span class="status-badge success">✓ Добавлено</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Пустое состояние -->
    <div v-if="!loading && publications.length === 0 && hasSearched" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>Публикации не найдены</p>
      <small>Попробуйте изменить параметры поиска</small>
    </div>

    <!-- Прогресс индикатор -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner-large"></div>
      <p>{{ loadingMessage }}</p>
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
      selectedPublications: [],
      addedPublications: [],
      loading: false,
      adding: false,
      error: null,
      hasSearched: false,
      loadingMessage: 'Загрузка публикаций...',
      currentYear: new Date().getFullYear()
    };
  },
  computed: {
    isValidOrcid() {
      const orcidPattern = /^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/;
      return orcidPattern.test(this.orcidInput);
    },
    allSelected() {
      return this.publications.length > 0 && 
             this.selectedPublications.length === this.publications.length;
    }
  },
  methods: {
    async importByOrcid() {
      if (!this.isValidOrcid) {
        this.error = 'Неверный формат ORCID. Ожидается: 0000-0000-0000-0000';
        return;
      }

      this.loading = true;
      this.error = null;
      this.hasSearched = true;
      this.loadingMessage = 'Загрузка публикаций из Crossref...';

      try {
        const response = await kpiAPI.syncCrossref({
          orcid: this.orcidInput,
          year: this.yearFilter
        });

        if (response.data.success) {
          this.publications = response.data.publications || [];
          
          if (this.publications.length === 0) {
            this.$toast.info('Публикации не найдены за указанный период');
          } else {
            this.$toast.success(`Найдено публикаций: ${this.publications.length}`);
          }
        } else {
          this.error = response.data.error || 'Не удалось загрузить публикации';
        }
      } catch (err) {
        console.error('Ошибка импорта по ORCID:', err);
        
        if (err.response?.status === 429) {
          this.error = 'Превышен лимит запросов. Пожалуйста, попробуйте позже.';
        } else if (err.response?.status === 504) {
          this.error = 'Превышено время ожидания. Попробуйте уменьшить диапазон поиска.';
        } else {
          this.error = err.response?.data?.error || 'Не удалось загрузить публикации';
        }
      } finally {
        this.loading = false;
      }
    },

    async importByDoi() {
      if (!this.doiInput) {
        this.error = 'Введите DOI публикации';
        return;
      }

      this.loading = true;
      this.error = null;
      this.hasSearched = true;
      this.loadingMessage = 'Поиск публикации по DOI...';

      try {
        // Используем эндпоинт для поиска по DOI
        const response = await this.$api.get('/kpi/crossref/search-by-doi/', {
          params: { doi: this.doiInput }
        });

        if (response.data) {
          this.publications = [response.data];
          this.$toast.success('Публикация найдена');
        } else {
          this.publications = [];
          this.error = 'Публикация с таким DOI не найдена';
        }
      } catch (err) {
        console.error('Ошибка поиска по DOI:', err);
        this.error = 'Не удалось найти публикацию. Проверьте правильность DOI.';
        this.publications = [];
      } finally {
        this.loading = false;
      }
    },

    async searchPublications() {
      if (!this.searchQuery) {
        this.error = 'Введите поисковый запрос';
        return;
      }

      this.loading = true;
      this.error = null;
      this.hasSearched = true;
      this.loadingMessage = 'Поиск публикаций...';

      try {
        const response = await this.$api.get('/kpi/crossref/search/', {
          params: { query: this.searchQuery }
        });

        this.publications = response.data.publications || [];
        
        if (this.publications.length === 0) {
          this.$toast.info('Публикации не найдены');
        } else {
          this.$toast.success(`Найдено публикаций: ${this.publications.length}`);
        }
      } catch (err) {
        console.error('Ошибка поиска:', err);
        this.error = 'Не удалось выполнить поиск. Попробуйте другой запрос.';
        this.publications = [];
      } finally {
        this.loading = false;
      }
    },

    toggleSelection(publication) {
      const index = this.selectedPublications.findIndex(p => p.doi === publication.doi);
      
      if (index > -1) {
        this.selectedPublications.splice(index, 1);
      } else {
        this.selectedPublications.push(publication);
      }
    },

    isSelected(publication) {
      return this.selectedPublications.some(p => p.doi === publication.doi);
    },

    selectAll() {
      if (this.allSelected) {
        this.selectedPublications = [];
      } else {
        this.selectedPublications = [...this.publications];
      }
    },

    async addSelectedPublications() {
      if (this.selectedPublications.length === 0) {
        this.$toast.warning('Выберите публикации для добавления');
        return;
      }

      this.adding = true;
      let successCount = 0;
      let errorCount = 0;
      let duplicateCount = 0;

      for (const pub of this.selectedPublications) {
        try {
          // Формируем данные для создания KpiValue
          const kpiData = {
            indicator_id: 1, // ID показателя "Публикации" - нужно получить динамически
            period: `${pub.year}-01`,
            actual_value: 1,
            comment: `${pub.title}\nЖурнал: ${pub.journal}\nDOI: ${pub.doi}`,
            // Можно добавить ссылку на DOI как подтверждение
          };

          await kpiAPI.createValue(kpiData);
          this.addedPublications.push(pub.doi);
          successCount++;
        } catch (error) {
          console.error(`Ошибка добавления публикации ${pub.doi}:`, error);
          
          // Проверяем, является ли ошибка дубликатом
          if (error.response?.status === 500 && 
              error.response?.data?.toString().includes('UNIQUE constraint')) {
            duplicateCount++;
            // Помечаем как уже добавленную
            this.addedPublications.push(pub.doi);
          } else {
            errorCount++;
          }
        }
      }

      this.adding = false;

      // Формируем сообщения
      const messages = [];
      if (successCount > 0) {
        messages.push(`Добавлено: ${successCount}`);
      }
      if (duplicateCount > 0) {
        messages.push(`Пропущено (уже есть): ${duplicateCount}`);
      }
      if (errorCount > 0) {
        messages.push(`Ошибок: ${errorCount}`);
      }

      if (messages.length > 0) {
        if (successCount > 0) {
          this.$toast.success(messages.join(', '));
          this.$emit('publications-added', successCount);
        } else if (duplicateCount > 0 && errorCount === 0) {
          this.$toast.info(messages.join(', '));
        } else {
          this.$toast.warning(messages.join(', '));
        }
      }
      
      // Очищаем выбранные
      this.selectedPublications = [];
    },

    formatPublicationType(type) {
      const types = {
        'journal-article': 'Статья в журнале',
        'proceedings-article': 'Статья в трудах конференции',
        'posted-content': 'Препринт',
        'book-chapter': 'Глава в книге'
      };
      return types[type] || type;
    },

    formatAuthors(authors) {
      if (authors.length <= 3) {
        return authors.join(', ');
      }
      return `${authors.slice(0, 3).join(', ')} и др.`;
    }
  }
};
</script>

<style scoped>
.crossref-import-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.import-header {
  text-align: center;
  margin-bottom: 32px;
}

.import-header h2 {
  margin: 0 0 8px 0;
  color: #2c3e50;
}

.subtitle {
  margin: 0;
  color: #7f8c8d;
  font-size: 1rem;
}

/* Вкладки */
.import-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 2px solid #e9ecef;
}

.tab-button {
  padding: 12px 24px;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: 500;
  color: #7f8c8d;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}

.tab-button:hover {
  color: #3498db;
}

.tab-button.active {
  color: #3498db;
  border-bottom-color: #3498db;
}

/* Контент вкладок */
.tab-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #2c3e50;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #7f8c8d;
  font-size: 0.85rem;
}

.btn-import {
  width: 100%;
  padding: 12px;
  font-size: 1rem;
}

/* Ошибки */
.error-block {
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.error-icon {
  font-size: 1.5rem;
}

.error-content {
  flex: 1;
}

.error-content h4 {
  margin: 0 0 8px 0;
  color: #c0392b;
}

.error-content p {
  margin: 0 0 12px 0;
  color: #e74c3c;
}

.btn-dismiss {
  padding: 4px 12px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

/* Результаты */
.results-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e9ecef;
}

.results-header h3 {
  margin: 0;
  color: #2c3e50;
}

.results-actions {
  display: flex;
  gap: 12px;
}

/* Список публикаций */
.publications-list {
  display: grid;
  gap: 16px;
}

.publication-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  transition: all 0.2s;
}

.publication-card:hover {
  border-color: #3498db;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
}

.publication-card.selected {
  background: #ebf5fb;
  border-color: #3498db;
}

.publication-select input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.publication-content {
  flex: 1;
}

.publication-title {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  line-height: 1.4;
}

.publication-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.meta-item strong {
  color: #2c3e50;
}

.publication-authors {
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.publication-links {
  display: flex;
  gap: 12px;
}

.link-doi {
  color: #3498db;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
}

.link-doi:hover {
  text-decoration: underline;
}

.publication-status {
  display: flex;
  align-items: center;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge.success {
  background: #d4edda;
  color: #155724;
}

/* Пустое состояние */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* Загрузка */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  color: white;
}

.spinner-large {
  border: 6px solid #f3f3f3;
  border-top: 6px solid #3498db;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Кнопки */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn:hover:not(:disabled) {
  opacity: 0.9;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-outline {
  background: transparent;
  border: 1px solid #95a5a6;
  color: #95a5a6;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.9rem;
}
</style>