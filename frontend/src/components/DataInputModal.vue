<template>
    <div class="modal-backdrop" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Добавление нового значения KPI</h3>
          <button class="close-button" @click="$emit('close')">&times;</button>
        </div>
        <form @submit.prevent="handleSubmit">
          <div class="modal-body">
            <!-- Выбор показателя -->
            <div class="form-group">
              <label for="indicator">Показатель KPI</label>
              <select id="indicator" v-model="formData.indicator_id" required>
                <option disabled value="">Выберите показатель</option>
                <option v-for="indicator in manualIndicators" :key="indicator.id" :value="indicator.id">
                  {{ indicator.group.name }}: {{ indicator.name }}
                </option>
              </select>
            </div>
  
            <!-- Период и Фактическое значение -->
            <div class="form-row">
              <div class="form-group">
                <label for="period">Период (ГГГГ-ММ)</label>
                <input type="text" id="period" v-model="formData.period" placeholder="2024-12" required pattern="\d{4}-\d{2}">
              </div>
              <div class="form-group">
                <label for="actual_value">Фактическое значение</label>
                <input type="number" id="actual_value" v-model.number="formData.actual_value" required step="any">
              </div>
            </div>
            
            <!-- Комментарий -->
            <div class="form-group">
              <label for="comment">Комментарий</label>
              <textarea id="comment" v-model="formData.comment" rows="3"></textarea>
            </div>
  
            <!-- Загрузка файла -->
            <div class="form-group">
              <label for="evidence">Подтверждающий документ (необязательно)</label>
              <input type="file" id="evidence" @change="handleFileChange">
            </div>
  
            <p v-if="error" class="error-message">{{ error }}</p>
          </div>
  
          <div class="modal-footer">
            <button type="button" class="btn btn-outline" @click="$emit('close')">Отмена</button>
            <button type="submit" class="btn btn-primary" :disabled="isLoading">
              {{ isLoading ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'DataInputModal',
    emits: ['close', 'data-saved'], // Объявляем события, которые компонент может отправлять родителю
    data() {
      return {
        manualIndicators: [], // Список KPI для ручного ввода
        formData: {
          indicator_id: '',
          period: new Date().toISOString().slice(0, 7), // По умолчанию текущий месяц
          actual_value: 0,
          comment: '',
        },
        selectedFile: null,
        isLoading: false,
        error: null,
      };
    },
    // Этот метод вызывается сразу после создания компонента
    async created() {
      await this.fetchManualIndicators();
    },
    methods: {
      // 1. Загружаем с бэкенда список показателей, которые можно вводить вручную
      async fetchManualIndicators() {
        try {
          const response = await this.$api.get('/kpi/indicators/manual/');
          this.manualIndicators = response.data;
        } catch (error) {
          console.error("Не удалось загрузить список показателей:", error);
          this.error = "Не удалось загрузить список показателей. Попробуйте позже.";
        }
      },
      // 2. Сохраняем выбранный файл
      handleFileChange(event) {
        this.selectedFile = event.target.files[0];
      },
      // 3. Отправляем данные на сервер
      async handleSubmit() {
        this.isLoading = true;
        this.error = null;
  
        // FormData используется для отправки файлов и данных формы вместе
        const submissionData = new FormData();
        submissionData.append('indicator_id', this.formData.indicator_id);
        submissionData.append('period', this.formData.period);
        submissionData.append('actual_value', this.formData.actual_value);
        submissionData.append('comment', this.formData.comment);
  
        if (this.selectedFile) {
          submissionData.append('evidence', this.selectedFile);
        }
        
        try {
          // Отправляем POST-запрос на эндпоинт, который создает новое значение KPI
          await this.$api.post('/kpi/values/', submissionData, {
            headers: {
              'Content-Type': 'multipart/form-data', // Важный заголовок для отправки файлов
            },
          });
          
          this.$toast.success('Данные успешно сохранены!');
          this.$emit('data-saved'); // Отправляем событие родителю, чтобы он обновил дашборд
          this.$emit('close'); // Отправляем событие, чтобы закрыть это окно
        } catch (err) {
          this.error = 'Произошла ошибка. Проверьте правильность введенных данных.';
          if (err.response && err.response.data) {
              // Пытаемся показать более конкретную ошибку с бэкенда
              this.error += ` (Сервер: ${JSON.stringify(err.response.data)})`;
          }
          this.$toast.error(this.error);
          console.error("Ошибка сохранения данных:", err);
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
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  .modal-content {
    background: white;
    border-radius: 8px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    width: 90%;
    max-width: 500px;
    display: flex;
    flex-direction: column;
  }
  .modal-header {
    padding: 16px;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .modal-header h3 {
    margin: 0;
  }
  .close-button {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
  }
  .modal-body {
    padding: 16px;
  }
  .form-group {
    margin-bottom: 1rem;
  }
  .form-row {
    display: flex;
    gap: 1rem;
  }
  .form-row .form-group {
    flex: 1;
  }
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }
  input[type="text"],
  input[type="number"],
  select,
  textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
  }
  .modal-footer {
    padding: 16px;
    border-top: 1px solid #e9ecef;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
  .error-message {
    color: #dc3545;
    font-size: 0.9rem;
  }
  /* Стили для кнопок */
  .btn { padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer; font-weight: 500; }
  .btn-primary { background-color: #007bff; color: white; }
  .btn-outline { background-color: transparent; border: 1px solid #6c757d; color: #6c757d; }
  .btn:disabled { background-color: #aaa; cursor: not-allowed; }
  </style>
  