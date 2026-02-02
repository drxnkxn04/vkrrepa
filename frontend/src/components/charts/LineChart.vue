<template>
    <div class="chart-container">
    <Line :data="data" :options="options" />
  </div>
  </template>
  
  <script>
  // Импортируем компонент Line из vue-chartjs
  import { Line } from 'vue-chartjs';
  
  // Импортируем необходимые элементы из Chart.js
  // Это ОБЯЗАТЕЛЬНО для Chart.js v3 и выше
  import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Filler  // ДОБАВИТЬ ЭТО!
} from 'chart.js';
  
  // Регистрируем импортированные элементы
  ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Filler  // ДОБАВИТЬ ЭТО!
);
  
export default {
  name: 'LineChart',
  components: { Line },
  props: {
    data: {
      type: Object,
      required: true
    },
    options: {
      type: Object,
      default: () => ({
        responsive: true,
        maintainAspectRatio: false
      })
    }
  }
};
  </script>

<style>
.chart-container {
  width: 100%;
  height: 400px; /* Фиксированная высота */
  /* Или можно использовать */
  /* max-height: 60vh; */ /* 60% от высоты viewport */
  position: relative;
}
</style>
  