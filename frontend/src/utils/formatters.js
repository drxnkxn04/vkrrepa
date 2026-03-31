// frontend/src/utils/formatters.js

const MONTH_NAMES_FULL = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
];

const MONTH_NAMES_SHORT = [
  'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
  'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек',
];

/**
 * Форматирует период YYYY-MM в читаемый вид.
 * @param {string} period - период в формате YYYY-MM
 * @param {boolean} short - использовать сокращённые названия месяцев
 * @returns {string}
 */
export function formatPeriod(period, short = false) {
  if (!period) return '—';
  const [year, month] = period.split('-');
  const names = short ? MONTH_NAMES_SHORT : MONTH_NAMES_FULL;
  return `${names[parseInt(month) - 1]} ${year}`;
}

/**
 * Форматирует число как валюту (RUB).
 * @param {number} amount
 * @returns {string}
 */
export function formatCurrency(amount) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Возвращает CSS-класс по проценту выполнения.
 * @param {number} score - процент (0-100)
 * @returns {string}
 */
export function getScoreClass(score) {
  if (score >= 90) return 'excellent';
  if (score >= 70) return 'good';
  if (score >= 50) return 'medium';
  return 'poor';
}
