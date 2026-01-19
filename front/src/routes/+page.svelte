<script>
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import Chart from 'chart.js/auto';

  let charts = [];
  let countByCategoryData = {};
  let brandDistributionData = {};
  let avgPriceByBrandData = {};
  let avgPriceByYearData = {};
  let brandReviewsData = {};

  const chartColors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#6B7280'];

  function createChart(id, config, onClick = null) {
    const ctx = document.getElementById(id);
    if (!ctx) return;

    const chart = new Chart(ctx, {
      ...config,
      options: {
        ...config.options,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#B0B0B0' }
          },
          ...config.options?.plugins
        },
        onClick: (evt, elements) => {
          if (onClick && elements.length > 0) {
            const clickedIndex = elements[0].index;
            onClick(clickedIndex, config.data.labels);
          }
        },
        onHover: (evt, elements) => {
          if (evt.native) {
            evt.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
          }
        }
      }
    });

    charts.push(chart);
    return chart;
  }

  function goToCategory(clickedIndex, labels) {
    const categoryName = labels[clickedIndex];
    goto(`/categories/${encodeURIComponent(categoryName)}`);
  }

  function goToBrand(clickedIndex, labels) {
    const brandName = labels[clickedIndex];
    goto(`/brands/${encodeURIComponent(brandName)}`);
  }

  function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU').format(num || 0);
  }

  async function fetchData() {
    if (!browser) return;

    const countResponse = await fetch(`http://localhost:8000/count`);
    const countData = await countResponse.json();
    countByCategoryData = countData.category_distribution || {};
    brandDistributionData = countData.brand_distribution || {};

    const priceResponse = await fetch(`http://localhost:8000/avg/price`);
    const priceData = await priceResponse.json();
    avgPriceByBrandData = priceData.avg_price_by_brand || {};
    avgPriceByYearData = priceData.avg_price_by_year || {};

    const reviewsResponse = await fetch(`http://localhost:8000/brand_by_reviews`);
    brandReviewsData = await reviewsResponse.json();

    charts.forEach(chart => chart.destroy());
    charts = [];

    // Диаграмма: Количество товаров по категориям (КРУГОВАЯ)
    createChart('countByCategory', {
      type: 'pie',
      data: {
        labels: Object.keys(countByCategoryData),
        datasets: [{
          data: Object.values(countByCategoryData),
          backgroundColor: chartColors,
          borderWidth: 1
        }]
      }
    }, goToCategory);

    // Диаграмма: Распределение по брендам
    createChart('brandDistribution', {
      type: 'pie',
      data: {
        labels: Object.keys(brandDistributionData),
        datasets: [{
          data: Object.values(brandDistributionData),
          backgroundColor: chartColors,
          borderWidth: 1
        }]
      }
    }, goToBrand);

    // Диаграмма: Средняя цена по брендам
    createChart('avgPriceByBrand', {
      type: 'bar',
      data: {
        labels: Object.keys(avgPriceByBrandData),
        datasets: [{
          label: 'Средняя цена',
          data: Object.values(avgPriceByBrandData),
          backgroundColor: '#10B981',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            ticks: { 
              color: '#B0B0B0',
              callback: function(value) {
                return formatNumber(value) + ' ₽';
              }
            },
            grid: { color: '#333333' }
          },
          x: {
            ticks: { color: '#B0B0B0' },
            grid: { color: '#333333' }
          }
        }
      }
    }, goToBrand);

    // Диаграмма: Средняя цена по годам
    createChart('avgPriceByYear', {
      type: 'line',
      data: {
        labels: Object.keys(avgPriceByYearData),
        datasets: [{
          label: 'Средняя цена',
          data: Object.values(avgPriceByYearData),
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        scales: {
          y: {
            ticks: { 
              color: '#B0B0B0',
              callback: function(value) {
                return formatNumber(value) + ' ₽';
              }
            },
            grid: { color: '#333333' }
          },
          x: {
            ticks: { color: '#B0B0B0' },
            grid: { color: '#333333' }
          }
        }
      }
    });

    // Топ брендов по количеству отзывов
    const topReviewedBrands = Object.entries(brandReviewsData)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    
    createChart('topReviewedBrands', {
      type: 'bar',
      data: {
        labels: topReviewedBrands.map(item => item[0]),
        datasets: [{
          label: 'Количество отзывов',
          data: topReviewedBrands.map(item => item[1]),
          backgroundColor: '#EF4444',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            ticks: { 
              color: '#B0B0B0',
              callback: function(value) {
                return formatNumber(value);
              }
            },
            grid: { color: '#333333' }
          },
          x: {
            ticks: { color: '#B0B0B0' },
            grid: { color: '#333333' }
          }
        }
      }
    }, goToBrand);

    // Топ брендов по средней цене
    const topPricedBrands = Object.entries(avgPriceByBrandData)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    
    createChart('topPricedBrands', {
      type: 'bar',
      data: {
        labels: topPricedBrands.map(item => item[0]),
        datasets: [{
          label: 'Средняя цена',
          data: topPricedBrands.map(item => item[1]),
          backgroundColor: '#3B82F6',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            ticks: { 
              color: '#B0B0B0',
              callback: function(value) {
                return formatNumber(value) + ' ₽';
              }
            },
            grid: { color: '#333333' }
          },
          x: {
            ticks: { color: '#B0B0B0' },
            grid: { color: '#333333' }
          }
        }
      }
    }, goToBrand);
  }

  onMount(() => {
    fetchData();
  });
</script>

<div class="dashboard-page">
  <div class="page-header">
    <h1>Анализ рынка</h1>
    <p>Глубокий анализ товаров в магазине DNS</p>
  </div>

  <div class="section">
    <h2>Общая статистика по рынку</h2>
    <div class="grid grid-2x2">
      <div class="card">
        <h3>Количество товаров по категориям</h3>
        <p class="chart-hint">Нажмите на сегмент для перехода к категории</p>
        <div style="height:300px"><canvas id="countByCategory"></canvas></div>
      </div>

      <div class="card">
        <h3>Распределение по брендам</h3>
        <p class="chart-hint">Нажмите на сегмент для перехода к бренду</p>
        <div style="height:300px"><canvas id="brandDistribution"></canvas></div>
      </div>

      <div class="card">
        <h3>Средняя цена по брендам</h3>
        <p class="chart-hint">Нажмите на столбец для перехода к бренду</p>
        <div style="height:300px"><canvas id="avgPriceByBrand"></canvas></div>
      </div>

      <div class="card">
        <h3>Средняя цена товаров по годам</h3>
        <div style="height:300px"><canvas id="avgPriceByYear"></canvas></div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>Популярность брендов</h2>
    <div class="grid grid-2x1">
      <div class="card">
        <h3>Топ-5 брендов по количеству отзывов</h3>
        <p class="chart-hint">Нажмите на столбец для перехода к бренду</p>
        <div style="height:300px"><canvas id="topReviewedBrands"></canvas></div>
      </div>

      <div class="card">
        <h3>Топ-5 брендов по средней цене</h3>
        <p class="chart-hint">Нажмите на столбец для перехода к бренду</p>
        <div style="height:300px"><canvas id="topPricedBrands"></canvas></div>
      </div>
    </div>
  </div>
</div>

<style>
  .dashboard-page {
    animation: fadeIn 0.5s ease;
  }

  .page-header {
    margin-bottom: 1.5rem;
  }

  .page-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--light-color);
    margin-bottom: 0.25rem;
  }

  .page-header p {
    font-size: 1rem;
    color: var(--gray-medium);
    margin: 0;
  }

  .section {
    margin-bottom: 2rem;
  }

  .section h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--light-color);
    margin-bottom: 1rem;
  }

  .grid-2x2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .grid-2x1 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .card {
    background: var(--dark-card);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--dark-border);
    padding: 1rem;
  }

  .card h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--light-color);
  }

  .chart-hint {
    font-size: 0.875rem;
    color: #9CA3AF;
    margin-top: -0.5rem;
    margin-bottom: 1rem;
    font-style: italic;
  }

  @media (max-width: 768px) {
    .page-header h1 {
      font-size: 1.75rem;
    }

    .card {
      padding: 0.75rem;
    }

    .card h3 {
      font-size: 1rem;
    }

    .grid-2x2,
    .grid-2x1 {
      grid-template-columns: 1fr;
    }
  }
</style>