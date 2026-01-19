<script>
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  let categoryName = '';
  let categoryData = null;
  let filteredDevices = [];
  let loading = true;
  let error = null;

  let minPrice = 0;
  let maxPrice = 0;
  let selectedSort = 'name_asc';
  let searchQuery = '';
  let minRating = 0;
  let maxReviews = 0;

  let realMaxPrice = 0;
  let realMaxReviews = 0;

  const sortOptions = [
    { value: 'name_asc', label: 'Название (А-Я)' },
    { value: 'name_desc', label: 'Название (Я-А)' },
    { value: 'price_asc', label: 'Цена (по возрастанию)' },
    { value: 'price_desc', label: 'Цена (по убыванию)' },
    { value: 'rating_desc', label: 'Рейтинг (высокий)' },
    { value: 'rating_asc', label: 'Рейтинг (низкий)' },
    { value: 'reviews_desc', label: 'Отзывы (много)' }
  ];

  $: {
    const decodedCategory = decodeURIComponent($page.params.category);
    if (decodedCategory !== categoryName) {
      categoryName = decodedCategory;
      loadCategoryData();
    }
  }

  async function loadCategoryData() {
    loading = true;
    error = null;
    try {
      const response = await fetch(`http://localhost:8000/products/category/${encodeURIComponent(categoryName)}`);
      if (!response.ok) throw new Error('Категория не найдена');
      
      const data = await response.json();

      categoryData = Object.values(data).map(item => ({
        ...item,
        id: parseInt(item.id) || item.id
      }));
      
      filteredDevices = [...categoryData];
      
      if (categoryData.length > 0) {
        const prices = categoryData.map(d => d.Цена || 0);
        minPrice = Math.min(...prices);
        maxPrice = Math.max(...prices);
        realMaxPrice = maxPrice;
        
        const reviews = categoryData.map(d => d.Всего_отзывов || 0);
        maxReviews = Math.max(...reviews);
        realMaxReviews = maxReviews;
      }
      
      applyFilters();
    } catch (err) {
      error = err.message;
      console.error('Ошибка загрузки данных:', err);
    } finally {
      loading = false;
    }
  }

  function applyFilters() {
    if (!categoryData || categoryData.length === 0) return;
    
    let filtered = [...categoryData];

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(device =>
        device.Наименование?.toLowerCase().includes(query)
      );
    }

    filtered = filtered.filter(device => {
      const price = device.Цена || 0;
      return price >= minPrice && price <= maxPrice;
    });

    filtered = filtered.filter(device => {
      const rating = device.Рейтинг || 0;
      return rating >= minRating;
    });

    filtered = filtered.filter(device => {
      const reviews = device.Всего_отзывов || 0;
      return reviews <= maxReviews;
    });

    filtered.sort((a, b) => {
      switch (selectedSort) {
        case 'name_asc':
          return (a.Наименование || '').localeCompare(b.Наименование || '');
        case 'name_desc':
          return (b.Наименование || '').localeCompare(a.Наименование || '');
        case 'price_asc':
          return (a.Цена || 0) - (b.Цена || 0);
        case 'price_desc':
          return (b.Цена || 0) - (a.Цена || 0);
        case 'rating_desc':
          return (b.Рейтинг || 0) - (a.Рейтинг || 0);
        case 'rating_asc':
          return (a.Рейтинг || 0) - (b.Рейтинг || 0);
        case 'reviews_desc':
          return (b.Всего_отзывов || 0) - (a.Всего_отзывов || 0);
        default:
          return 0;
      }
    });
    
    filteredDevices = filtered;
  }

  function handleSearch(e) {
    searchQuery = e.target.value;
    applyFilters();
  }

  function handlePriceChange() {
    applyFilters();
  }

  function handleSortChange(value) {
    selectedSort = value;
    applyFilters();
  }

  function handleRatingChange(e) {
    minRating = parseFloat(e.target.value);
    applyFilters();
  }

  function handleReviewsChange(e) {
    maxReviews = parseInt(e.target.value);
    applyFilters();
  }

  function resetFilters() {
    if (!categoryData || categoryData.length === 0) return;
    
    minPrice = 0;
    maxPrice = realMaxPrice;
    
    maxReviews = realMaxReviews;
    
    searchQuery = '';
    minRating = 0;
    selectedSort = 'name_asc';
    
    applyFilters();
  }

  function goToProduct(productId) {
    goto(`/devices/${productId}`);
  }

  function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU').format(num || 0);
  }

  function formatPrice(price) {
    return formatNumber(price) + ' ₽';
  }

  function calculateCategoryStats() {
    if (!categoryData || categoryData.length === 0) return null;
    
    const devices = categoryData;
    const avgRating = devices.reduce((sum, d) => sum + (d.Рейтинг || 0), 0) / devices.length;
    const avgPrice = devices.reduce((sum, d) => sum + (d.Цена || 0), 0) / devices.length;
    const totalReviews = devices.reduce((sum, d) => sum + (d.Всего_отзывов || 0), 0);

    const brandCounts = {};
    devices.forEach(device => {
      const name = device.Наименование || '';
      let brand = 'Неизвестно';

      if (name.includes('Apple')) brand = 'Apple';
      else if (name.includes('Samsung')) brand = 'Samsung';
      else if (name.includes('Xiaomi') || name.includes('Redmi') || name.includes('Poco')) brand = 'Xiaomi';
      else if (name.includes('Huawei')) brand = 'Huawei';
      else if (name.includes('Honor')) brand = 'Honor';
      else if (name.includes('Realme')) brand = 'Realme';
      else if (name.includes('OnePlus')) brand = 'OnePlus';
      else if (name.includes('Google') || name.includes('Pixel')) brand = 'Google';
      else if (name.includes('Nokia')) brand = 'Nokia';
      else if (name.includes('Motorola')) brand = 'Motorola';
      else if (name.includes('Asus') || name.includes('ROG') || name.includes('ZenFone')) brand = 'Asus';
      else if (name.includes('Sony') || name.includes('Xperia')) brand = 'Sony';
      else if (name.includes('Lenovo')) brand = 'Lenovo';
      else if (name.includes('OPPO')) brand = 'OPPO';
      else if (name.includes('Vivo')) brand = 'Vivo';
      else if (name.includes('Tecno')) brand = 'Tecno';
      else if (name.includes('Infinix')) brand = 'Infinix';
      else brand = 'Другой';
      
      brandCounts[brand] = (brandCounts[brand] || 0) + 1;
    });
    
    let topBrand = 'Неизвестно';
    let maxCount = 0;
    Object.entries(brandCounts).forEach(([brand, count]) => {
      if (count > maxCount) {
        maxCount = count;
        topBrand = brand;
      }
    });
    
    const topBrandShare = ((maxCount / devices.length) * 100).toFixed(1);
    
    return {
      avgRating,
      avgPrice,
      totalReviews,
      topBrand,
      topBrandShare,
      deviceCount: devices.length
    };
  }

  const stats = calculateCategoryStats();
</script>

<div class="category-page">
  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Загрузка данных о категории...</p>
    </div>
  {:else if error}
    <div class="error">
      <h2>Ошибка</h2>
      <p>{error}</p>
      <button on:click={loadCategoryData}>Попробовать снова</button>
    </div>
  {:else if categoryData && categoryData.length > 0}
    <div class="category-header">
      <h1>{categoryName}</h1>
      
      <div class="category-stats">
        <div class="stat-card">
          <div class="stat-value">{formatNumber(categoryData.length)}</div>
          <div class="stat-label">Товаров</div>
        </div>
        
        {#if stats}
          <div class="stat-card">
            <div class="stat-value">{stats.avgRating.toFixed(1)}</div>
            <div class="stat-label">Средний рейтинг</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-value">{formatPrice(stats.avgPrice)}</div>
            <div class="stat-label">Средняя цена</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-value">{formatNumber(stats.totalReviews)}</div>
            <div class="stat-label">Отзывов</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-value">{stats.topBrand}</div>
            <div class="stat-label">Топ бренд ({stats.topBrandShare}%)</div>
          </div>
        {/if}
      </div>
    </div>

    <div class="main-layout">
      <div class="products-section">
        <div class="search-container">
          <div class="search-box">
            <input
              type="text"
              placeholder="Поиск товаров..."
              bind:value={searchQuery}
              on:input={handleSearch}
            />
            <svg class="search-icon" viewBox="0 0 24 24">
              <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
          </div>
          
          <div class="results-info">
            Найдено товаров: <strong>{filteredDevices.length}</strong> из {categoryData.length}
            {#if filteredDevices.length === 0}
              <span class="no-results-text"> - ничего не найдено</span>
            {/if}
          </div>
        </div>

        <div class="products-grid">
          {#each filteredDevices as device}
            <div class="product-card" on:click={() => goToProduct(device.id)}>
              <div class="product-image">
                <div class="image-placeholder">?</div>
              </div>
              
              <div class="product-info">
                <h3 class="product-title">{device.Наименование}</h3>
                
                <div class="product-rating">
                  <div class="stars">
                    {#each Array(5) as _, i}
                      <span class="star {i < Math.floor(device.Рейтинг || 0) ? 'filled' : ''}">
                        ★
                      </span>
                    {/each}
                    <span class="rating-value">({(device.Рейтинг || 0).toFixed(1)})</span>
                  </div>
                  <div class="reviews">{formatNumber(device.Всего_отзывов || 0)} отзывов</div>
                </div>
                
                <div class="product-price">
                  {formatPrice(device.Цена || 0)}
                </div>
                
                <button class="view-btn">Подробнее</button>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="filters-sidebar">
        <div class="filters-header">
          <h3>Фильтры</h3>
          <button on:click={resetFilters} class="reset-btn">Сбросить</button>
        </div>

        <div class="filter-section">
          <h4>Сортировка</h4>
          <div class="radio-group">
            {#each sortOptions as option}
              <label class="radio-label">
                <input
                  type="radio"
                  name="sort"
                  value={option.value}
                  checked={selectedSort === option.value}
                  on:change={() => handleSortChange(option.value)}
                />
                <span class="radio-custom"></span>
                <span class="radio-text">{option.label}</span>
              </label>
            {/each}
          </div>
        </div>

        <div class="filter-section">
          <h4>Цена</h4>
          <div class="price-range">
            <div class="price-labels">
              <span>{formatPrice(minPrice)}</span>
              <span>{formatPrice(maxPrice)}</span>
            </div>
            <div class="range-slider">
              <input
                type="range"
                min={0}
                max={realMaxPrice || 100000}
                step={1000}
                bind:value={minPrice}
                on:input={handlePriceChange}
              />
              <input
                type="range"
                min={0}
                max={realMaxPrice || 100000}
                step={1000}
                bind:value={maxPrice}
                on:input={handlePriceChange}
              />
            </div>
          </div>
        </div>

        <div class="filter-section">
          <h4>Рейтинг от {minRating.toFixed(1)}</h4>
          <div class="rating-filter">
            <div class="stars-display">
              {#each Array(5) as _, i}
                <span class="star {i < Math.floor(minRating) ? 'filled' : ''}">★</span>
              {/each}
            </div>
            <input
              type="range"
              min={0}
              max={5}
              step={0.5}
              bind:value={minRating}
              on:input={handleRatingChange}
              class="rating-slider"
            />
          </div>
        </div>

        <div class="filter-section">
          <h4>Макс. отзывов: {maxReviews}</h4>
          <div class="reviews-filter">
            <input
              type="range"
              min={0}
              max={realMaxReviews || 100}
              step={1}
              bind:value={maxReviews}
              on:input={handleReviewsChange}
              class="reviews-slider"
            />
          </div>
        </div>
      </div>
    </div>
  {:else if categoryData && categoryData.length === 0}
    <div class="empty-state">
      <h2>Категория пуста</h2>
      <p>В категории "{categoryName}" пока нет товаров</p>
      <button on:click={() => goto('/samsung')}>Вернуться на главную</button>
    </div>
  {:else}
    <div class="empty-state">
      <h2>Данные не загружены</h2>
      <button on:click={loadCategoryData}>Загрузить данные</button>
    </div>
  {/if}
</div>

<style>
  .category-page {
    padding: 2rem;
    max-width: 1600px;
    margin: 0 auto;
  }

  .category-header {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--dark-border);
  }

  .category-header h1 {
    font-size: 2.5rem;
    color: white;
    margin-bottom: 1.5rem;
  }

  .category-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: var(--dark-card);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    text-align: center;
    border: 1px solid var(--dark-border);
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color, #3B82F6);
    margin-bottom: 0.5rem;
  }

  .stat-label {
    font-size: 0.9rem;
    color: var(--gray-medium);
  }

  .main-layout {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 2rem;
    align-items: start;
  }

  .products-section {
    min-width: 0;
  }

  .search-container {
    background: var(--dark-card);
    border-radius: var(--border-radius);
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    border: 1px solid var(--dark-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1.5rem;
  }

  .search-box {
    position: relative;
    flex-grow: 1;
  }

  .search-box input {
    width: 100%;
    padding: 0.75rem 1rem 0.75rem 3rem;
    background: var(--dark-bg);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    color: white;
    font-size: 1rem;
  }

  .search-icon {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    width: 1.25rem;
    height: 1.25rem;
    fill: var(--gray-medium);
  }

  .results-info {
    color: var(--light-color);
    white-space: nowrap;
  }

  .results-info strong {
    color: var(--primary-color);
  }

  .no-results-text {
    color: var(--gray-medium);
    font-style: italic;
  }

  .products-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.5rem;
  }

  .product-card {
    background: var(--dark-card);
    border-radius: var(--border-radius);
    overflow: hidden;
    border: 1px solid var(--dark-border);
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: pointer;
  }

  .product-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary-color);
  }

  .product-image {
    height: 200px;
    background: var(--dark-bg);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .image-placeholder {
    width: 100px;
    height: 100px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    font-weight: bold;
    color: white;
  }

  .product-info {
    padding: 1.5rem;
  }

  .product-title {
    font-size: 1.1rem;
    color: white;
    margin-bottom: 1rem;
    line-height: 1.4;
    height: 2.8rem;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .product-rating {
    margin-bottom: 1rem;
  }

  .stars {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin-bottom: 0.25rem;
  }

  .star {
    color: #6B7280;
    font-size: 1.1rem;
  }

  .star.filled {
    color: #F59E0B;
  }

  .rating-value {
    margin-left: 0.5rem;
    color: var(--gray-medium);
    font-size: 0.9rem;
  }

  .reviews {
    color: var(--gray-medium);
    font-size: 0.9rem;
  }

  .product-price {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 1rem;
  }

  .view-btn {
    width: 100%;
    padding: 0.75rem;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .view-btn:hover {
    background: #2563EB;
  }

  .filters-sidebar {
    background: var(--dark-card);
    border-radius: var(--border-radius);
    border: 1px solid var(--dark-border);
    padding: 1.5rem;
    position: sticky;
    top: 2rem;
  }

  .filters-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--dark-border);
  }

  .filters-header h3 {
    font-size: 1.5rem;
    color: white;
    margin: 0;
  }

  .reset-btn {
    padding: 0.5rem 1rem;
    background: transparent;
    color: var(--primary-color);
    border: 1px solid var(--primary-color);
    border-radius: var(--border-radius);
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
  }

  .reset-btn:hover {
    background: var(--primary-color);
    color: white;
  }

  .filter-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--dark-border);
  }

  .filter-section:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }

  .filter-section h4 {
    font-size: 1.1rem;
    color: white;
    margin-bottom: 1rem;
  }

  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .radio-label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: var(--border-radius);
    transition: background 0.2s;
  }

  .radio-label:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .radio-label input {
    display: none;
  }

  .radio-custom {
    width: 18px;
    height: 18px;
    border: 2px solid var(--primary-color);
    border-radius: 50%;
    position: relative;
    flex-shrink: 0;
  }

  .radio-label input:checked + .radio-custom::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 10px;
    height: 10px;
    background: var(--primary-color);
    border-radius: 50%;
  }

  .radio-text {
    color: var(--light-color);
    font-size: 0.95rem;
  }

  .price-range {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .price-labels {
    display: flex;
    justify-content: space-between;
    color: var(--gray-medium);
    font-size: 0.9rem;
  }

  .range-slider {
    position: relative;
    height: 20px;
  }

  .range-slider input[type="range"] {
    position: absolute;
    width: 100%;
    background: transparent;
    pointer-events: none;
  }

  .range-slider input[type="range"]::-webkit-slider-thumb {
    pointer-events: all;
  }

  .rating-filter {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .stars-display {
    display: flex;
    gap: 0.25rem;
    font-size: 1.25rem;
  }

  .stars-display .star {
    color: #6B7280;
  }

  .stars-display .star.filled {
    color: #F59E0B;
  }

  .rating-slider {
    width: 100%;
  }

  .reviews-slider {
    width: 100%;
  }

  .loading, .error, .empty-state {
    text-align: center;
    padding: 4rem 2rem;
  }

  .spinner {
    width: 50px;
    height: 50px;
    border: 4px solid var(--dark-border);
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error button, .empty-state button {
    margin-top: 1rem;
    padding: 0.75rem 2rem;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
  }

  @media (max-width: 1400px) {
    .products-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  @media (max-width: 1200px) {
    .main-layout {
      grid-template-columns: 1fr;
    }
    
    .filters-sidebar {
      position: static;
    }
    
    .search-container {
      flex-direction: column;
      align-items: stretch;
      gap: 1rem;
    }
    
    .results-info {
      text-align: center;
    }
  }

  @media (max-width: 900px) {
    .products-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 768px) {
    .category-page {
      padding: 1rem;
    }

    .category-header h1 {
      font-size: 2rem;
    }

    .category-stats {
      grid-template-columns: repeat(2, 1fr);
    }

    .products-grid {
      grid-template-columns: 1fr;
    }
  }
</style>