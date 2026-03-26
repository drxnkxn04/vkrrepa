<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <div class="modal-title-block">
          <h3>{{ isEditMode ? 'Редактирование значения KPI' : 'Добавление значения KPI' }}</h3>
          <span v-if="isEditMode" class="edit-hint">Показатель и период изменить нельзя</span>
        </div>
        <button class="close-button" @click="$emit('close')">&times;</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="modal-body">

          <!-- Выбор показателя -->
          <div class="form-group">
            <label for="indicator">Показатель KPI <span class="required">*</span></label>
            <select
              id="indicator"
              v-model="formData.indicator_id"
              required
              :disabled="isEditMode"
              @change="onIndicatorChange"
            >
              <option disabled value="">Выберите показатель</option>
              <optgroup
                v-for="group in groupedIndicators"
                :key="group.name"
                :label="group.name"
              >
                <option
                  v-for="ind in group.indicators"
                  :key="ind.id"
                  :value="ind.id"
                >
                  {{ ind.name }}
                </option>
              </optgroup>
            </select>
            <div v-if="selectedIndicatorInfo" class="indicator-hint">
              <span v-if="selectedIndicatorInfo.unit">Единица: <strong>{{ selectedIndicatorInfo.unit }}</strong></span>
              <span v-if="selectedIndicatorInfo.max_value"> · Плановое значение: <strong>{{ selectedIndicatorInfo.max_value }}</strong></span>
            </div>
          </div>

          <!-- Период -->
          <div class="form-group">
            <label for="period">Период <span class="required">*</span></label>
            <input
              type="month"
              id="period"
              v-model="formData.period"
              required
              :disabled="isEditMode"
            >
          </div>

          <!-- Фактическое значение -->
          <div class="form-group">
            <label for="actual_value">
              Фактическое значение <span class="required">*</span>
              <span v-if="selectedIndicatorInfo?.unit" class="unit-label">({{ selectedIndicatorInfo.unit }})</span>
            </label>
            <input
              type="number"
              id="actual_value"
              v-model.number="formData.actual_value"
              required
              step="any"
              min="0"
              :placeholder="selectedIndicatorInfo ? `Максимум: ${selectedIndicatorInfo.max_value}` : ''"
            >
          </div>

          <!-- Комментарий -->
          <div class="form-group">
            <label for="comment">Комментарий</label>
            <textarea
              id="comment"
              v-model="formData.comment"
              rows="3"
              placeholder="Опишите как был достигнут результат, добавьте ссылки или пояснения..."
            ></textarea>
          </div>

          <!-- Файл -->
          <div class="form-group">
            <label>Подтверждающий документ</label>
            <div class="file-upload-area" @click="$refs.fileInput.click()">
              <span v-if="!selectedFile" class="file-placeholder">
                Нажмите чтобы прикрепить файл (PDF, Word, изображение)
              </span>
              <span v-else class="file-selected">
                📎 {{ selectedFile.name }}
                <button type="button" class="file-remove" @click.stop="selectedFile = null">✕</button>
              </span>
            </div>
            <input ref="fileInput" type="file" class="file-hidden" @change="handleFileChange">
          </div>

          <p v-if="error" class="error-message">{{ error }}</p>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-outline" @click="$emit('close')">Отмена</button>
          <button type="submit" class="btn btn-primary" :disabled="isLoading">
            {{ isLoading ? 'Сохранение...' : (isEditMode ? 'Сохранить изменения' : 'Добавить') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { kpiAPI } from '@/services/api';

export default {
  name: 'DataInputModal',
  emits: ['close', 'data-saved'],
  props: {
    editValue: { type: Object, default: null }
  },
  data() {
    return {
      manualIndicators: [],
      formData: {
        indicator_id: '',
        period: new Date().toISOString().slice(0, 7),
        actual_value: 0,
        comment: '',
      },
      selectedFile: null,
      isLoading: false,
      error: null,
    };
  },
  computed: {
    isEditMode() {
      return !!this.editValue;
    },
    groupedIndicators() {
      const groups = {};
      for (const ind of this.manualIndicators) {
        const gName = ind.group?.name || 'Прочее';
        if (!groups[gName]) groups[gName] = { name: gName, indicators: [] };
        groups[gName].indicators.push(ind);
      }
      return Object.values(groups);
    },
    selectedIndicatorInfo() {
      if (!this.formData.indicator_id) return null;
      return this.manualIndicators.find(i => i.id === this.formData.indicator_id) || null;
    },
  },
  async created() {
    await this.fetchManualIndicators();
    if (this.editValue) {
      this.formData.indicator_id = this.editValue.indicator?.id || '';
      this.formData.period = this.editValue.period || '';
      this.formData.actual_value = this.editValue.actual_value ?? 0;
      this.formData.comment = this.editValue.comment || '';
    }
  },
  methods: {
    async fetchManualIndicators() {
      try {
        const response = await kpiAPI.getManualIndicators();
        this.manualIndicators = response.data;
      } catch (error) {
        console.error('Не удалось загрузить список показателей:', error);
        this.error = 'Не удалось загрузить список показателей. Попробуйте позже.';
      }
    },
    onIndicatorChange() {
      // сбрасываем значение при смене показателя
      this.formData.actual_value = 0;
    },
    handleFileChange(event) {
      this.selectedFile = event.target.files[0] || null;
    },
    async handleSubmit() {
      this.isLoading = true;
      this.error = null;

      try {
        if (this.isEditMode) {
          const patchData = {
            actual_value: this.formData.actual_value,
            comment: this.formData.comment,
          };
          if (this.selectedFile) {
            const fd = new FormData();
            fd.append('actual_value', this.formData.actual_value);
            fd.append('comment', this.formData.comment);
            fd.append('evidence', this.selectedFile);
            await kpiAPI.updateValue(this.editValue.id, fd);
          } else {
            await kpiAPI.updateValue(this.editValue.id, patchData);
          }
          this.$toast.success('Данные успешно обновлены!');
        } else {
          const submissionData = {
            indicator_id: this.formData.indicator_id,
            period: this.formData.period,
            actual_value: this.formData.actual_value,
            comment: this.formData.comment,
          };
          if (this.selectedFile) {
            submissionData.evidence = this.selectedFile;
          }
          await kpiAPI.createValue(submissionData);
          this.$toast.success('Данные успешно сохранены!');
        }

        this.$emit('data-saved');
        this.$emit('close');
      } catch (err) {
        this.error = 'Произошла ошибка. Проверьте правильность введённых данных.';
        if (err.response?.data) {
          const data = err.response.data;
          const msgs = Object.values(data).flat().join('; ');
          if (msgs) this.error = msgs;
        }
        this.$toast.error(this.error);
      } finally {
        this.isLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  padding: 20px;
}
.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 580px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.modal-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.modal-title-block h3 { margin: 0 0 4px; font-size: 1.1rem; }
.edit-hint { font-size: 0.78rem; color: #888; }
.close-button {
  background: none;
  border: none;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #aaa;
  padding: 0;
  margin-left: 12px;
}
.close-button:hover { color: #333; }
.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group { display: flex; flex-direction: column; gap: 6px; }
label {
  font-weight: 600;
  font-size: 0.88rem;
  color: #444;
}
.required { color: #dc3545; }
.unit-label { font-weight: 400; color: #888; font-size: 0.85rem; }
select,
input[type="month"],
input[type="number"],
textarea {
  width: 100%;
  padding: 9px 12px;
  border: 1.5px solid #dee2e6;
  border-radius: 7px;
  font-size: 0.92rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
  font-family: inherit;
}
select:focus,
input:focus,
textarea:focus {
  outline: none;
  border-color: #007bff;
}
select:disabled,
input:disabled {
  background: #f8f9fa;
  color: #888;
  cursor: not-allowed;
}
textarea { resize: vertical; min-height: 80px; }
.indicator-hint { font-size: 0.8rem; color: #666; background: #f8f9fa; padding: 6px 10px; border-radius: 5px; }
.file-upload-area {
  border: 2px dashed #dee2e6;
  border-radius: 7px;
  padding: 14px 16px;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;
}
.file-upload-area:hover { border-color: #007bff; background: #f0f7ff; }
.file-placeholder { color: #aaa; font-size: 0.88rem; }
.file-selected { color: #495057; font-size: 0.88rem; display: flex; align-items: center; justify-content: center; gap: 8px; }
.file-remove { background: none; border: none; color: #dc3545; cursor: pointer; font-size: 1rem; padding: 0; }
.file-hidden { display: none; }
.error-message {
  color: #dc3545;
  background: #f8d7da;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 0.88rem;
  margin: 0;
}
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
/* Кнопки — глобальные стили в App.vue */
.btn-primary:disabled { background: #a0c4f1; }
</style>
