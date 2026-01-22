<template>
    <Line :data="data" :options="options" />
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
    PointElement
  } from 'chart.js';
  
  // Регистрируем импортированные элементы
  ChartJS.register(
    Title,
    Tooltip,
    Legend,
    LineElement,
    CategoryScale,
    LinearScale,
    PointElement
  );
  
  export default {
    name: 'LineChart',
    components: {
      Line // Регистрируем компонент Line для использования в шаблоне
    },
    // 'props' позволяют передавать данные в этот компонент из родительского (Dashboard.vue)
    props: {
      data: {
        type: Object,
        required: true
      },
      options: {
        type: Object,
        // Опции не всегда обязательны, можно задать по умолчанию
        default: () => ({
          responsive: true,
          maintainAspectRatio: false
        })
      }
    }
  };
  </script>
  