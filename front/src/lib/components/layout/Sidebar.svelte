<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  const menuItems = [
    { path: '/', label: 'Анализ рынка', src: '/phone.png' }
  ];

  const categoryColors = [
    '#4285F4',
    '#EA4335',
    '#FBBC05',
    '#34A853',
    '#8B5CF6',
    '#EC4899',
    '#10B981',
    '#F59E0B',
    '#EF4444',
    '#3B82F6',
    '#8B5CF6',
    '#EC4899',
    '#F97316',
    '#84CC16',
    '#06B6D4',
    '#6366F1',
    '#D946EF',
    '#14B8A6',
    '#F43F5E',
    '#0EA5E9',
    '#A855F7',
    '#E11D48',
    '#2563EB',
    '#7C3AED',
    '#DC2626',
    '#059669',
    '#D97706',
    '#DB2777'
  ];

  let categories = $state([
    { name: 'Загрузка...', count: 0, color: '#4285F4' }
  ]);

  let showAllCategories = $state(false);
  let totalCategories = $state(0);

  let info = $state([
    { name: 'total_product', count: '—' },
    { name: 'total_comment', count: '—' },
    { name: 'last_parsing_date', count: '—' },
    { name: 'last_parsing_time', count: '—' }
  ]);

  let imagesLoaded = $state({});

  function getVisibleCategories() {
    return showAllCategories ? categories : categories.slice(0, 5);
  }

  function navigate(path, event) {
    if (event) event.preventDefault();
    goto(path);
  }

  function goToCategory(categoryName, event) {
    if (event) event.preventDefault();
    const encodedCategory = encodeURIComponent(categoryName);
    goto(`/categories/${encodedCategory}`);
  }

  function formatLastParsing(dateString) {
    if (!dateString) return { date: '—', time: '—' };
    
    try {
      const date = new Date(dateString);
      
      // Форматируем дату: Год Месяц День
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const formattedDate = `${year}.${month}.${day}`;
      
      // Форматируем время: Часы:Минуты
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const formattedTime = `${hours}:${minutes}`;
      
      return {
        date: formattedDate,
        time: formattedTime
      };
    } catch (error) {
      console.error('Ошибка форматирования даты:', error);
      return { date: '—', time: '—' };
    }
  }
  
  async function fetchCategories() {
    try {
      const response = await fetch('http://localhost:8000/count');
      const data = await response.json();
      
      if (data.category_distribution) {
        const categoryEntries = Object.entries(data.category_distribution);
        totalCategories = categoryEntries.length;

        categoryEntries.sort((a, b) => b[1] - a[1]);

        const formattedCategories = categoryEntries.map(([name, count], index) => ({
          name,
          count,
          color: categoryColors[index % categoryColors.length]
        }));
        
        categories.length = 0;
        categories.push(...formattedCategories);
      }
    } catch (error) {
      console.error('Ошибка получения категорий:', error);
      categories.length = 0;
      categories.push({ name: 'Ошибка загрузки', count: 0, color: '#EA4335' });
    }
  }
  
  async function fetchInfo() {
    try {
      const response = await fetch('http://localhost:8000/info');
      const data = await response.json();
      
      for (let i = 0; i < info.length; i++) {
        if (info[i].name === 'total_product') {
          info[i].count = data.total_products?.toString() ?? '0';
        } else if (info[i].name === 'total_comment') {
          info[i].count = data.total_reviews?.toString() ?? '0';
        } else if (info[i].name === 'last_parsing_date') {
          const formatted = formatLastParsing(data.last_parsing);
          info[i].count = formatted.date;
        } else if (info[i].name === 'last_parsing_time') {
          const formatted = formatLastParsing(data.last_parsing);
          info[i].count = formatted.time;
        }
      }
    } catch (error) {
      console.error('Ошибка получения info:', error);
    }
  }

  function toggleCategories() {
    showAllCategories = !showAllCategories;
  }

  function preloadImages() {
    menuItems.forEach(item => {
      const img = new Image();
      img.src = item.src;
      img.onload = () => {
        imagesLoaded[item.src] = true;
      };
      img.onerror = () => {
        console.warn(`Не удалось загрузить изображение: ${item.src}`);
        imagesLoaded[item.src] = false;
      };
    });
  }

  $effect(() => {
    if (browser) {
      fetchInfo();
      fetchCategories();
      preloadImages();

      const infoInterval = setInterval(fetchInfo, 60000);
      const categoriesInterval = setInterval(fetchCategories, 120000);
      
      return () => {
        clearInterval(infoInterval);
        clearInterval(categoriesInterval);
      };
    }
  });
</script>

<aside class="sidebar">
  <nav class="sidebar-nav">
    <ul class="nav-menu">
      {#each menuItems as item}
        <li class="nav-item">
          <a 
            href={item.path} 
            class:active={$page.url.pathname === item.path}
            on:click|preventDefault={(e) => navigate(item.path, e)}
            on:mouseenter={() => {
              if (!imagesLoaded[item.src]) {
                const img = new Image();
                img.src = item.src;
              }
            }}
          >
            <span class="nav-icon">
              {#if imagesLoaded[item.src] !== false}
                <img 
                  src={item.src} 
                  alt={item.label} 
                  style="width: 32px; height: 32px; object-fit: contain;"
                  on:error={() => {
                    imagesLoaded[item.src] = false;
                  }}
                />
              {:else}
                <div class="icon-fallback">
                  {item.label.charAt(0)}
                </div>
              {/if}
            </span>
            <span class="nav-label">{item.label}</span>
            {#if $page.url.pathname === item.path}
              <span class="nav-indicator"></span>
            {/if}
          </a>
        </li>
      {/each}
    </ul>
  </nav>
  
  <div class="sidebar-section">
    <div class="section-header">
      <h4 class="section-title">Категории</h4>
      {#if totalCategories > 5}
        <button 
          class="toggle-categories-btn" 
          on:click={toggleCategories}
          title={showAllCategories ? 'Показать меньше' : 'Показать все'}
        >
          {showAllCategories ? 'Свернуть' : `Все (${totalCategories})`}
        </button>
      {/if}
    </div>
    <div class="categories-list" class:scrollable={showAllCategories}>
      {#each getVisibleCategories() as category}
        <a 
          href="/categories/{category.name}" 
          class="category-item"
          on:click|preventDefault={(e) => goToCategory(category.name, e)}
          title="Кликните для деталей категории"
        >
          <div class="category-info">
            <div class="category-color" style="background-color: {category.color};"></div>
            <span class="category-name">{category.name}</span>
          </div>
          <span class="category-count">{category.count}</span>
        </a>
      {/each}
    </div>
  </div>
  
  <div class="sidebar-footer">
    <div class="data-stats">
      <div class="stat-item">
        <span class="stat-label">Всего товаров:</span>
        <span class="stat-value">{info[0].count}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Всего комментариев:</span>
        <span class="stat-value">{info[1].count}</span>
      </div>
      <div class="last-parsing-item">
        <span class="last-parsing-label">Последнее обновление:</span>
        <div class="last-parsing-values">
          <span class="last-parsing-date">{info[2].count}</span>
          <span class="last-parsing-time">{info[3].count}</span>
        </div>
      </div>
    </div>
  </div>
</aside>

<style>
  .sidebar {
    background: var(--dark-card);
    width: 280px;
    height: calc(100vh - 70px);
    position: fixed;
    left: 0;
    top: 70px;
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    z-index: 90;
    overflow-y: auto;
    border-right: 1px solid var(--dark-border);
  }
  
  .sidebar-nav {
    padding: 2rem 0;
    flex: 1;
  }
  
  .nav-menu {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .nav-item {
    margin: 0;
  }
  
  .nav-item a {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    text-decoration: none;
    color: var(--gray-medium);
    font-weight: 500;
    transition: all 0.3s ease;
    position: relative;
    cursor: pointer;
  }
  
  .nav-item a:hover {
    background-color: var(--gray-100);
    color: var(--primary-color);
  }
  
  .nav-item a.active {
    background-color: var(--primary-bg);
    color: var(--primary-color);
    font-weight: 600;
  }
  
  .nav-icon {
    font-size: 1.25rem;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  
  .nav-icon img {
    display: block;
    transition: opacity 0.3s ease;
  }
  
  .nav-item a:hover .nav-icon img {
    opacity: 0.9;
  }
  
  .nav-item a.active .nav-icon img {
    filter: brightness(1.2);
  }
  
  .icon-fallback {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: white;
    font-size: 14px;
  }
  
  .nav-label {
    flex: 1;
  }
  
  .nav-indicator {
    width: 4px;
    height: 20px;
    background-color: var(--primary-color);
    border-radius: 2px;
    position: absolute;
    right: 0;
  }
  
  .sidebar-section {
    padding: 1.5rem;
    border-top: 1px solid var(--dark-border);
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .section-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--gray-medium);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0;
  }
  
  .toggle-categories-btn {
    background: transparent;
    border: none;
    color: var(--primary-color);
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    transition: background-color 0.2s ease;
  }
  
  .toggle-categories-btn:hover {
    background-color: var(--primary-bg);
  }
  
  .categories-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-height: 200px;
    transition: max-height 0.3s ease;
  }
  
  .categories-list.scrollable {
    overflow-y: auto;
    max-height: 300px;
  }

  .categories-list::-webkit-scrollbar {
    width: 4px;
  }
  
  .categories-list::-webkit-scrollbar-track {
    background: var(--gray-100);
    border-radius: 2px;
  }
  
  .categories-list::-webkit-scrollbar-thumb {
    background: var(--gray-300);
    border-radius: 2px;
  }
  
  .categories-list::-webkit-scrollbar-thumb:hover {
    background: var(--gray-400);
  }
  
  .category-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem;
    border-radius: 4px;
    transition: all 0.3s ease;
    text-decoration: none;
    cursor: pointer;
    color: inherit;
  }
  
  .category-item:hover {
    background-color: var(--gray-100);
    transform: translateX(2px);
    box-shadow: var(--shadow-sm);
  }
  
  .category-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
    min-width: 0;
  }
  
  .category-color {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  .category-name {
    font-size: 0.875rem;
    color: var(--gray-medium);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .category-count {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--light-color);
    background-color: var(--gray-200);
    padding: 0.25rem 0.5rem;
    border-radius: 10px;
    flex-shrink: 0;
    margin-left: 0.5rem;
  }
  
  .sidebar-footer {
    padding: 1.5rem;
    border-top: 1px solid var(--dark-border);
    background-color: var(--gray-100);
  }
  
  .data-stats {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .last-parsing-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }
  
  .last-parsing-label {
    font-size: 0.75rem;
    color: var(--gray-medium);
    flex-shrink: 0;
  }
  
  .last-parsing-values {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.125rem;
  }
  
  .last-parsing-date {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--light-color);
  }
  
  .last-parsing-time {
    font-size: 0.75rem;
    color: var(--gray-medium);
  }
  
  .stat-label {
    font-size: 0.75rem;
    color: var(--gray-medium);
  }
  
  .stat-value {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--light-color);
  }
  
  @media (max-width: 1024px) {
    .sidebar {
      width: 100%;
      height: auto;
      position: static;
      margin-bottom: 2rem;
      box-shadow: none;
      border-bottom: 1px solid var(--dark-border);
    }
    
    .sidebar-nav {
      padding: 1rem 0;
    }
    
    .nav-menu {
      display: flex;
      justify-content: center;
      gap: 1rem;
    }
    
    .nav-item a {
      padding: 0.5rem 1rem;
      border-radius: 20px;
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .nav-indicator {
      display: none;
    }
    
    .sidebar-section,
    .sidebar-footer {
      display: none;
    }
  }
</style>