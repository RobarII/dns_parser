<script>
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  let deviceId = '';
  let productData = null;
  let loading = true;
  let error = null;
  let activeTab = 'specs';

  $: {
    deviceId = $page.params.device;
    loadProductData();
  }

  async function loadProductData() {
    loading = true;
    error = null;
    try {
      const response = await fetch(`http://localhost:8000/products/${deviceId}`);
      if (!response.ok) throw new Error('Товар не найден');
      
      productData = await response.json();
    } catch (err) {
      error = err.message;
      console.error('Ошибка загрузки товара:', err);
    } finally {
      loading = false;
    }
  }

  function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU').format(price || 0) + ' ₽';
  }

  function formatRating(rating) {
    return rating?.toFixed(1) || '0.0';
  }

  function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU').format(num || 0);
  }

  function goBack() {
    history.back();
  }
</script>

<div class="device-page">
  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Загрузка информации о товаре...</p>
    </div>
  {:else if error}
    <div class="error">
      <h2>Ошибка</h2>
      <p>{error}</p>
      <button on:click={loadProductData}>Попробовать снова</button>
      <button on:click={goBack} class="back-btn">Вернуться назад</button>
    </div>
  {:else if productData}
    <button class="back-button" on:click={goBack}>
      ← Назад
    </button>

    <div class="device-container">
      <div class="device-main">
        <div class="device-header">
          <h1 class="device-title">{productData.Наименование}</h1>
          
          <div class="device-meta">
            {#if productData.Категория}
              <span class="category">{productData.Категория}</span>
            {/if}
            {#if productData.Характеристики?.Год_релиза}
              <span class="year">{productData.Характеристики.Год_релиза} год</span>
            {/if}
            {#if productData.Характеристики?.Бренд}
              <span class="brand">{productData.Характеристики.Бренд}</span>
            {/if}
          </div>

          <div class="rating-price-section">
            <div class="rating">
              <div class="stars">
                {#each Array(5) as _, i}
                  <span class="star {i < Math.floor(productData.Рейтинг || 0) ? 'filled' : ''}">
                    ★
                  </span>
                {/each}
                <span class="rating-value">{formatRating(productData.Рейтинг)}</span>
              </div>
              {#if productData.Всего_отзывов > 0}
                <div class="reviews-count">{formatNumber(productData.Всего_отзывов)} отзывов</div>
              {/if}
            </div>
            
            <div class="price-section">
              <div class="current-price">{formatPrice(productData.Цена)}</div>
            </div>
          </div>
        </div>

        <div class="tabs">
          <button 
            class:active={activeTab === 'description'}
            on:click={() => activeTab = 'description'}
          >
            Описание
          </button>
          <button 
            class:active={activeTab === 'specs'}
            on:click={() => activeTab = 'specs'}
          >
            Характеристики
          </button>
        </div>

        <div class="tab-content">
          {#if activeTab === 'description'}
            <div class="description">
              {#if productData.Описание}
                <p>{productData.Описание}</p>
              {:else}
                <p class="no-data">Описание отсутствует</p>
              {/if}
            </div>
          {:else if activeTab === 'specs'}
            <div class="specifications">
              {#if productData.Характеристики && Object.keys(productData.Характеристики).length > 0}
                <div class="specs-grid">
                  {#each Object.entries(productData.Характеристики) as [key, value]}
                    {#if value !== null && value !== ''}
                      <div class="spec-row">
                        <div class="spec-key">{key.replace(/_/g, ' ')}</div>
                        <div class="spec-value">{value}</div>
                      </div>
                    {/if}
                  {/each}
                </div>
              {:else}
                <p class="no-data">Характеристики отсутствуют</p>
              {/if}
            </div>
          {/if}
        </div>
      </div>

      <div class="device-sidebar">
        <div class="device-image">
          <div class="image-container">
            <div class="image-placeholder">
              <div class="brand-logo">
                {productData.Характеристики?.Бренд?.charAt(0) || productData.Наименование?.charAt(0) || 'P'}
              </div>
            </div>
          </div>
        </div>

        <div class="additional-info">
          <h3>Информация о товаре</h3>
          
          <div class="info-grid">
            {#if productData.id}
              <div class="info-item">
                <span class="info-label">ID товара:</span>
                <span class="info-value">#{productData.id}</span>
              </div>
            {/if}
            
            {#if productData.Рейтинг}
              <div class="info-item">
                <span class="info-label">Рейтинг:</span>
                <span class="info-value rating-badge">
                  {formatRating(productData.Рейтинг)}
                  <span class="stars-small">
                    {#each Array(5) as _, i}
                      <span class:filled={i < Math.floor(productData.Рейтинг)}>★</span>
                    {/each}
                  </span>
                </span>
              </div>
            {/if}
            
            {#if productData.Всего_отзывов !== undefined}
              <div class="info-item">
                <span class="info-label">Отзывов:</span>
                <span class="info-value">{formatNumber(productData.Всего_отзывов)}</span>
              </div>
            {/if}
            
            {#if productData.Цена}
              <div class="info-item">
                <span class="info-label">Цена:</span>
                <span class="info-value price-highlight">{formatPrice(productData.Цена)}</span>
              </div>
            {/if}
            
            {#if productData.Категория}
              <div class="info-item">
                <span class="info-label">Категория:</span>
                <span class="info-value">{productData.Категория}</span>
              </div>
            {/if}
            
            {#if productData.Характеристики?.Модель}
              <div class="info-item">
                <span class="info-label">Модель:</span>
                <span class="info-value">{productData.Характеристики.Модель}</span>
              </div>
            {/if}
            
            {#if productData.Характеристики?.Тип}
              <div class="info-item">
                <span class="info-label">Тип:</span>
                <span class="info-value">{productData.Характеристики.Тип}</span>
              </div>
            {/if}
            
            {#if productData.Характеристики?.Гарантия_продавца}
              <div class="info-item">
                <span class="info-label">Гарантия:</span>
                <span class="info-value">{productData.Характеристики.Гарантия_продавца}</span>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  {:else}
    <div class="empty-state">
      <h2>Товар не найден</h2>
      <button on:click={goBack}>Вернуться назад</button>
    </div>
  {/if}
</div>

<style>
  .device-page {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
    min-height: calc(100vh - 70px);
  }

  .back-button {
    margin-bottom: 2rem;
    padding: 0.75rem 1.5rem;
    background: transparent;
    border: 1px solid var(--dark-border);
    color: var(--light-color);
    border-radius: var(--border-radius);
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.2s;
  }

  .back-button:hover {
    background: var(--dark-border);
  }

  .device-container {
    display: grid;
    grid-template-columns: 1fr 350px;
    gap: 3rem;
    margin-top: 1rem;
  }

  .device-main {
    min-width: 0;
  }

  .device-header {
    margin-bottom: 2rem;
  }

  .device-title {
    font-size: 2.2rem;
    color: white;
    margin-bottom: 1rem;
    line-height: 1.3;
  }

  .device-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .category, .year, .brand {
    background: var(--dark-card);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    color: var(--gray-medium);
  }

  .rating-price-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    background: var(--dark-card);
    border-radius: var(--border-radius);
    border: 1px solid var(--dark-border);
  }

  .rating {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .stars {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .star {
    color: #6B7280;
    font-size: 1.5rem;
  }

  .star.filled {
    color: #F59E0B;
  }

  .rating-value {
    margin-left: 0.5rem;
    font-size: 1.2rem;
    font-weight: 700;
    color: white;
  }

  .reviews-count {
    color: var(--gray-medium);
    font-size: 0.9rem;
  }

  .price-section {
    text-align: right;
  }

  .current-price {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--primary-color);
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid var(--dark-border);
    margin-bottom: 2rem;
    gap: 0.5rem;
  }

  .tabs button {
    padding: 1rem 1.5rem;
    background: none;
    border: none;
    color: var(--gray-medium);
    font-size: 1rem;
    cursor: pointer;
    position: relative;
    transition: color 0.2s;
    border-bottom: 3px solid transparent;
  }

  .tabs button:hover {
    color: white;
  }

  .tabs button.active {
    color: var(--primary-color);
    border-bottom-color: var(--primary-color);
  }

  .tab-content {
    background: var(--dark-card);
    border-radius: var(--border-radius);
    padding: 2rem;
    border: 1px solid var(--dark-border);
  }

  .description p {
    color: var(--gray-medium);
    line-height: 1.6;
    margin-bottom: 1rem;
  }

  .specs-grid {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .spec-row {
    display: grid;
    grid-template-columns: 250px 1fr;
    gap: 1rem;
    padding: 1rem;
    background: var(--dark-bg);
    border-radius: var(--border-radius);
    border: 1px solid var(--dark-border);
  }

  .spec-key {
    color: var(--gray-medium);
    font-weight: 500;
  }

  .spec-value {
    color: white;
    font-weight: 400;
  }

  .no-data {
    color: var(--gray-medium);
    font-style: italic;
    text-align: center;
    padding: 2rem;
  }

  .device-sidebar {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    position: sticky;
    top: 2rem;
    align-self: start;
  }

  .device-image {
    background: var(--dark-card);
    border-radius: var(--border-radius);
    overflow: hidden;
    border: 1px solid var(--dark-border);
  }

  .image-container {
    padding: 2rem;
  }

  .image-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 250px;
  }

  .brand-logo {
    width: 180px;
    height: 180px;
    background: linear-gradient(135deg, var(--primary-color) 0%, #8B5CF6 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3.5rem;
    font-weight: bold;
    color: white;
  }

  .additional-info {
    background: var(--dark-card);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    border: 1px solid var(--dark-border);
  }

  .additional-info h3 {
    color: white;
    margin-bottom: 1.5rem;
    font-size: 1.3rem;
  }

  .info-grid {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--dark-border);
  }

  .info-item:last-child {
    border-bottom: none;
  }

  .info-label {
    color: var(--gray-medium);
    font-size: 0.9rem;
  }

  .info-value {
    color: white;
    font-weight: 500;
    text-align: right;
  }

  .rating-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .stars-small {
    font-size: 0.8rem;
    color: #6B7280;
  }

  .stars-small .filled {
    color: #F59E0B;
  }

  .price-highlight {
    color: var(--primary-color);
    font-weight: 700;
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

  .back-btn {
    margin-left: 1rem;
    background: transparent;
    border: 1px solid var(--dark-border);
  }

  @media (max-width: 1200px) {
    .device-container {
      grid-template-columns: 1fr;
      gap: 2rem;
    }
    
    .device-sidebar {
      position: static;
    }
    
    .spec-row {
      grid-template-columns: 1fr;
      gap: 0.5rem;
    }
  }

  @media (max-width: 768px) {
    .device-page {
      padding: 1rem;
    }

    .device-title {
      font-size: 1.8rem;
    }

    .rating-price-section {
      flex-direction: column;
      align-items: flex-start;
      gap: 1.5rem;
    }

    .price-section {
      text-align: left;
    }

    .tabs {
      flex-direction: column;
      border-bottom: none;
    }

    .tabs button {
      border-bottom: none;
      border-left: 3px solid transparent;
      text-align: left;
    }

    .tabs button.active {
      border-left-color: var(--primary-color);
      border-bottom-color: transparent;
    }

    .brand-logo {
      width: 150px;
      height: 150px;
      font-size: 3rem;
    }
  }

  @media (max-width: 480px) {
    .device-meta {
      flex-direction: column;
      align-items: flex-start;
    }

    .rating-value {
      font-size: 1.2rem;
    }

    .current-price {
      font-size: 2rem;
    }

    .tab-content {
      padding: 1rem;
    }
  }
</style>