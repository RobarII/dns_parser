<script>
  import { page } from '$app/stores';
  import { onMount, onDestroy } from 'svelte';
  
  let chatOpen = $state(false);
  let chatMessages = $state([
    { id: 1, text: 'Привет! Я могу подсказать какие плюсы и минусы у конкретного устройства', isBot: true, timestamp: new Date() }
  ]);
  let userInput = $state('');
  let isLoading = $state(false);
  let chatAbortController = null;
  
  function toggleChat() {
    chatOpen = !chatOpen;
    if (chatOpen && chatMessages.length === 1) {
      setTimeout(() => {
        const chatContainer = document.querySelector('.chat-messages');
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      }, 100);
    }
  }
  
  async function sendMessage() {
    if (!userInput.trim() || isLoading) return;
    
    console.log('🔄 Начало отправки сообщения:', userInput);
    
    if (chatAbortController) {
      console.log('⚠️ Отмена предыдущего запроса');
      chatAbortController.abort();
    }
    
    const userMessage = {
      id: chatMessages.length + 1,
      text: userInput,
      isBot: false,
      timestamp: new Date()
    };
    
    chatMessages = [...chatMessages, userMessage];
    const userInputText = userInput;
    userInput = '';
    isLoading = true;
    
    chatAbortController = new AbortController();
    
    const timeoutId = setTimeout(() => {
      if (chatAbortController) {
        console.log('⏰ Таймаут 120 секунд, отмена запроса');
        chatAbortController.abort();
      }
    }, 120000);
    
    try {
      const encodedPrompt = encodeURIComponent(userInputText);
      const apiUrl = `http://localhost:8000/ai/?q=${encodedPrompt}`;
      
      console.log('📡 Отправка запроса к API:', apiUrl);
      
      const response = await fetch(apiUrl, {
        signal: chatAbortController.signal,
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      clearTimeout(timeoutId);
      
      console.log('✅ Ответ получен, статус:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Ошибка HTTP:', response.status, errorText);
        throw new Error(`HTTP ошибка ${response.status}`);
      }
      
      const responseText = await response.text();
      console.log('📄 Ответ:', responseText);
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('❌ Ошибка парсинга JSON');
        data = { response: responseText };
      }
      
      const aiResponse = data.response || data.answer || data.text || data.message || 
                        data.result || responseText || "Не удалось получить ответ от AI";
      
      console.log('🤖 Ответ AI:', aiResponse);
      
      const botMessage = {
        id: chatMessages.length + 2,
        text: aiResponse,
        isBot: true,
        timestamp: new Date()
      };
      
      chatMessages = [...chatMessages, botMessage];
      
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        console.log('⏹️ Запрос отменен');
        
        const cancelMessage = {
          id: chatMessages.length + 2,
          text: 'Запрос отменен. Возможно, модель долго обрабатывает запрос.',
          isBot: true,
          timestamp: new Date(),
          isInfo: true
        };
        
        chatMessages = [...chatMessages, cancelMessage];
      } else {
        console.error('❌ Ошибка:', error);
        
        const errorMessage = {
          id: chatMessages.length + 2,
          text: `Ошибка: ${error.message || 'неизвестная ошибка'}`,
          isBot: true,
          timestamp: new Date(),
          isError: true
        };
        
        chatMessages = [...chatMessages, errorMessage];
      }
    } finally {
      console.log('🏁 Завершение');
      isLoading = false;
      chatAbortController = null;
      
      setTimeout(() => {
        const chatContainer = document.querySelector('.chat-messages');
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      }, 100);
    }
  }
  
  function cancelRequest() {
    if (chatAbortController) {
      chatAbortController.abort();
      isLoading = false;
      chatAbortController = null;
      
      const cancelMessage = {
        id: chatMessages.length + 1,
        text: 'Запрос отменен',
        isBot: true,
        timestamp: new Date(),
        isInfo: true
      };
      
      chatMessages = [...chatMessages, cancelMessage];
    }
  }
  
  function sendExampleQuestion(question) {
    userInput = question;
    setTimeout(() => sendMessage(), 100);
  }
  
  function formatTime(date) {
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
  
  function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }
  
  function handleClickOutside(e) {
    if (chatOpen && 
        !e.target.closest('.chat-widget') && 
        !e.target.closest('.chat-button')) {
      chatOpen = false;
    }
  }
  
  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
      if (chatAbortController) {
        chatAbortController.abort();
      }
    };
  });
</script>

<header class="header">
  <div class="header-left">
    <a href="/samsung" class="logo-link">
      <div class="logo">
        <h1 class="logo-text">Панель мониторинга</h1>
      </div>
    </a>
  </div>

  <div class="header-center">
    <div class="page-title">
      {#if $page.url.pathname.includes('samsung')}
        Анализ рынка
      {:else if $page.url.pathname.includes('parser')}
        Панель мониторинга парсера
      {:else if $page.url.pathname.includes('brands')}
        Детали бренда
      {:else if $page.url.pathname.includes('categories')}
        Детали категорий
      {/if}
    </div>
  </div>
  
  <div class="header-right">
    <button class="chat-button" on:click={toggleChat} title="AI ассистент">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <span class="chat-badge" class:hidden={chatMessages.length <= 1}>AI</span>
    </button>
  </div>
</header>

{#if chatOpen}
  <div class="chat-widget">
    <div class="chat-header">
      <h3>AI Ассистент</h3>
      <div class="chat-header-actions">
        {#if isLoading}
          <button class="cancel-button" on:click={cancelRequest} title="Отменить запрос">
            ✕
          </button>
        {/if}
        <button class="chat-close" on:click={toggleChat}>×</button>
      </div>
    </div>
    
    <div class="chat-messages">
      {#each chatMessages as message}
        <div class="message {message.isBot ? 'bot' : 'user'} {message.isError ? 'error' : ''} {message.isInfo ? 'info' : ''}">
          <div class="message-content">
            <div class="message-text">{message.text}</div>
            <div class="message-time">{formatTime(message.timestamp)}</div>
          </div>
        </div>
      {/each}
      
      {#if isLoading}
        <div class="message bot">
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
              <span class="typing-text">AI обрабатывает запрос...</span>
            </div>
          </div>
        </div>
      {/if}
    </div>
    
    <div class="chat-input">
      <textarea
        bind:value={userInput}
        placeholder="Вопрос для AI..."
        rows="1"
        on:keydown={handleKeyPress}
        autocomplete="off"
        spellcheck="false"
        disabled={isLoading}
      ></textarea>
      <button class="send-button" on:click={sendMessage} disabled={isLoading || !userInput.trim()}>
        {#if isLoading}
          <div class="spinner"></div>
        {:else}
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        {/if}
      </button>
    </div>
  </div>
{/if}

<style>
  .header {
    background: var(--dark-card);
    box-shadow: var(--shadow-md);
    padding: 0 2rem;
    height: 70px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 1px solid var(--dark-border);
  }
  
  .header-left {
    display: flex;
    align-items: center;
  }
  
  .logo-link {
    text-decoration: none;
    display: inline-block;
  }
  
  .logo-link:hover .logo-text {
    color: var(--primary-color);
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .logo-text {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--light-color);
    cursor: pointer;
    transition: color 0.2s ease;
    white-space: nowrap;
  }
  
  .header-center {
    flex: none;
    display: block;
    margin: 0;
  }
  
  .page-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--primary-color);
    white-space: nowrap;
  }

  .header-right {
    flex: none;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 1rem;
  }

  .chat-button {
    position: relative;
    background: var(--primary-color);
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: white;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
  }
  
  .chat-button:hover {
    background: #2563EB;
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(59, 130, 246, 0.4);
  }
  
  .chat-button:active {
    transform: translateY(0);
  }
  
  .chat-badge {
    position: absolute;
    top: -5px;
    right: -5px;
    background: #10B981;
    color: white;
    font-size: 0.7rem;
    font-weight: bold;
    border-radius: 10px;
    padding: 2px 6px;
    min-width: 20px;
    text-align: center;
  }
  
  .chat-badge.hidden {
    display: none;
  }

  .chat-widget {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    height: 500px;
    background: var(--dark-card);
    border-radius: 12px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    z-index: 1000;
    border: 1px solid var(--dark-border);
    animation: slideIn 0.3s ease;
  }
  
  @keyframes slideIn {
    from {
      transform: translateY(20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
  
  .chat-header {
    padding: 1rem 1.5rem;
    background: linear-gradient(135deg, var(--primary-color), #2563EB);
    border-radius: 12px 12px 0 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .chat-header h3 {
    margin: 0;
    color: white;
    font-size: 1.1rem;
    font-weight: 600;
  }
  
  .chat-header-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  
  .cancel-button {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    font-size: 0.9rem;
    cursor: pointer;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background-color 0.2s ease;
  }
  
  .cancel-button:hover {
    background: rgba(255, 255, 255, 0.3);
  }
  
  .chat-close {
    background: transparent;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    line-height: 1;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background-color 0.2s ease;
  }
  
  .chat-close:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .chat-messages {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .chat-messages::-webkit-scrollbar {
    width: 6px;
  }
  
  .chat-messages::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .chat-messages::-webkit-scrollbar-thumb {
    background: var(--gray-400);
    border-radius: 3px;
  }
  
  .message {
    display: flex;
    max-width: 85%;
  }
  
  .message.user {
    align-self: flex-end;
  }
  
  .message.bot {
    align-self: flex-start;
  }
  
  .message-content {
    padding: 0.75rem 1rem;
    border-radius: 12px;
  }
  
  .message.user .message-content {
    background: var(--primary-color);
    color: white;
  }
  
  .message.bot .message-content {
    background: var(--gray-100);
    color: var(--light-color);
  }
  
  .message.error .message-content {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #FCA5A5;
  }
  
  .message.info .message-content {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    color: #93C5FD;
  }
  
  .message-text {
    font-size: 0.95rem;
    line-height: 1.4;
    margin-bottom: 0.25rem;
  }
  
  .message-time {
    font-size: 0.7rem;
    opacity: 0.7;
    text-align: right;
  }
  
  .typing-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0.5rem;
  }
  
  .typing-indicator span {
    width: 8px;
    height: 8px;
    background: var(--gray-400);
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
  }
  
  .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
  .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
  
  .typing-text {
    font-size: 0.85rem;
    color: var(--gray-medium);
  }
  
  @keyframes typing {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
    40% { transform: scale(1); opacity: 1; }
  }
  
  .chat-input {
    padding: 1rem;
    display: flex;
    gap: 0.5rem;
    align-items: flex-end;
  }
  
  .chat-input textarea {
    flex: 1;
    background: var(--gray-100);
    border: 1px solid var(--dark-border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: var(--light-color);
    font-size: 0.95rem;
    resize: none;
    min-height: 44px;
  }
  
  .chat-input textarea:focus {
    outline: none;
    border-color: var(--primary-color);
  }
  
  .send-button {
    background: var(--primary-color);
    border: none;
    border-radius: 8px;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: white;
  }
  
  .send-button:disabled {
    opacity: 0.5;
  }
  
  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  @media (max-width: 1024px) {
    .header {
      padding: 1rem;
      flex-direction: column;
      height: auto;
      gap: 1rem;
    }
    
    .header-left,
    .header-center,
    .header-right {
      width: 100%;
      justify-content: center;
    }
    
    .logo-text {
      font-size: 1.3rem;
    }
    
    .chat-widget {
      width: calc(100% - 40px);
      height: 450px;
      bottom: 10px;
      right: 10px;
      left: 10px;
    }
    
    .chat-button {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
    }
  }
</style>