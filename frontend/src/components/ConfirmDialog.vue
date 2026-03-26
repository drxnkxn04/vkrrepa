<template>
  <transition name="confirm-fade">
    <div v-if="visible" class="confirm-backdrop" @click.self="cancel">
      <div class="confirm-box">
        <h3>{{ title }}</h3>
        <p>{{ message }}</p>
        <div class="confirm-actions">
          <button class="btn btn-cancel" @click="cancel">Отмена</button>
          <button class="btn" :class="dangerClass" @click="confirm">
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'ConfirmDialog',
  props: {
    visible: { type: Boolean, default: false },
    title: { type: String, default: 'Подтверждение' },
    message: { type: String, default: 'Вы уверены?' },
    confirmText: { type: String, default: 'Подтвердить' },
    danger: { type: Boolean, default: false },
  },
  emits: ['confirm', 'cancel'],
  computed: {
    dangerClass() {
      return this.danger ? 'btn-danger' : 'btn-primary';
    },
  },
  methods: {
    confirm() {
      this.$emit('confirm');
    },
    cancel() {
      this.$emit('cancel');
    },
  },
};
</script>

<style scoped>
.confirm-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.confirm-box {
  background: white;
  border-radius: 10px;
  padding: 28px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.confirm-box h3 {
  margin: 0 0 10px;
  font-size: 1.1rem;
  color: #1a202c;
}

.confirm-box p {
  margin: 0 0 24px;
  color: #4b5563;
  font-size: 0.93rem;
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Кнопки — глобальные стили в App.vue */

.confirm-fade-enter-active,
.confirm-fade-leave-active {
  transition: opacity 0.15s;
}

.confirm-fade-enter-from,
.confirm-fade-leave-to {
  opacity: 0;
}
</style>
