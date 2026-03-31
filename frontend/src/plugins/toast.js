// frontend/src/plugins/toast.js

class ToastService {
    constructor() {
      this.container = null;
      this.toasts = [];
      this.idCounter = 0;
    }
  
    init() {
      // Создаем контейнер для уведомлений
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  
    show(message, type = 'info', duration = 3000) {
      const id = ++this.idCounter;
      
      const toast = document.createElement('div');
      toast.className = `toast toast-${type} toast-enter`;
      toast.setAttribute('data-toast-id', id);
      
      // Иконки для разных типов
      const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
      };
      
      const iconEl = document.createElement('div');
      iconEl.className = 'toast-icon';
      iconEl.textContent = icons[type] || icons.info;

      const messageEl = document.createElement('div');
      messageEl.className = 'toast-message';
      messageEl.textContent = message;

      const closeBtn = document.createElement('button');
      closeBtn.className = 'toast-close';
      closeBtn.textContent = '\u00d7';
      closeBtn.addEventListener('click', () => this.remove(toast));

      toast.appendChild(iconEl);
      toast.appendChild(messageEl);
      toast.appendChild(closeBtn);
      
      this.container.appendChild(toast);
      
      // Анимация появления
      requestAnimationFrame(() => {
        toast.classList.remove('toast-enter');
        toast.classList.add('toast-visible');
      });
      
      // Автоудаление
      if (duration > 0) {
        setTimeout(() => {
          this.remove(toast);
        }, duration);
      }
      
      return id;
    }
  
    remove(toast) {
      if (!toast) return;
      
      toast.classList.remove('toast-visible');
      toast.classList.add('toast-exit');
      
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }
  
    success(message, duration) {
      return this.show(message, 'success', duration);
    }
  
    error(message, duration) {
      return this.show(message, 'error', duration);
    }
  
    warning(message, duration) {
      return this.show(message, 'warning', duration);
    }
  
    info(message, duration) {
      return this.show(message, 'info', duration);
    }
  
    clear() {
      while (this.container.firstChild) {
        this.container.removeChild(this.container.firstChild);
      }
    }
  }
  
  // CSS стили (инжектируем в head)
  const styles = `
  .toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-width: 400px;
    pointer-events: none;
  }
  
  .toast {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border-left: 4px solid;
    pointer-events: auto;
    min-width: 300px;
    opacity: 0;
    transform: translateX(400px);
    transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  }
  
  .toast-visible {
    opacity: 1;
    transform: translateX(0);
  }
  
  .toast-exit {
    opacity: 0;
    transform: translateX(400px);
  }
  
  .toast-success {
    border-left-color: #28a745;
  }
  
  .toast-error {
    border-left-color: #dc3545;
  }
  
  .toast-warning {
    border-left-color: #ffc107;
  }
  
  .toast-info {
    border-left-color: #17a2b8;
  }
  
  .toast-icon {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 16px;
    color: white;
  }
  
  .toast-success .toast-icon {
    background: #28a745;
  }
  
  .toast-error .toast-icon {
    background: #dc3545;
  }
  
  .toast-warning .toast-icon {
    background: #ffc107;
  }
  
  .toast-info .toast-icon {
    background: #17a2b8;
  }
  
  .toast-message {
    flex: 1;
    color: #2c3e50;
    font-size: 14px;
    line-height: 1.4;
  }
  
  .toast-close {
    flex-shrink: 0;
    background: none;
    border: none;
    color: #95a5a6;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: all 0.2s;
  }
  
  .toast-close:hover {
    background: #f8f9fa;
    color: #2c3e50;
  }
  
  @media (max-width: 480px) {
    .toast-container {
      left: 10px;
      right: 10px;
      top: 10px;
      max-width: none;
    }
    
    .toast {
      min-width: auto;
    }
  }
  `;
  
  // Создаем и инжектируем стили
  const styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
  
  // Создаем глобальный экземпляр
  const toastService = new ToastService();
  
  // Vue 3 плагин
  export default {
    install(app) {
      toastService.init();
      
      // Добавляем в globalProperties для Options API
      app.config.globalProperties.$toast = toastService;
      
      // Предоставляем для Composition API
      app.provide('toast', toastService);
    }
  };
  
  // Экспортируем также сам сервис для использования вне Vue
  export { toastService };