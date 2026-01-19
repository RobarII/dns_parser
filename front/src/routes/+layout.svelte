<script>
  import Header from '$lib/components/layout/Header.svelte';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  
  import '../lib/styles/global.css';

</script>

<svelte:head>
  <title>DNS Analytics Dashboard</title>
  <meta name="description" content="Real-time analytics dashboard for DNS Shop data" />
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" href="/favicon.ico" />
</svelte:head>

<Header />
<Sidebar />

<main class="main-content">
  <div class="container">
      <slot />
  </div>
</main>

<style>
  .main-content {
    margin-left: 280px;
    margin-top: 70px;
    padding: 2rem;
    min-height: calc(100vh - 70px);
    background-color: var(--darker-color);
  }
  
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(10, 10, 10, 0.95);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .loading-spinner {
    width: 50px;
    height: 50px;
    border: 4px solid var(--gray-300);
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }
  
  .loading-overlay p {
    font-size: 1.1rem;
    color: var(--gray-light);
    font-weight: 500;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  @media (max-width: 1024px) {
    .main-content {
      margin-left: 0;
      margin-top: 0;
      padding: 1rem;
    }
  }
</style>