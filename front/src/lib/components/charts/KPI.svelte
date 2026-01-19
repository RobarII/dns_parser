<script>
  export let title = '';
  export let value = '';
  export let icon = '';
  export let trend = null;
  export let color = 'primary';
  
  const colors = {
    primary: '#4285F4',
    secondary: '#34A853',
    accent: '#EA4335',
    warning: '#FBBC05'
  };
</script>

<div class="kpi-card" style="border-left: 4px solid {colors[color]};">
  <div class="kpi-header">
    {#if $$slots.icon}
      <slot name="icon"></slot>
    {:else if icon}
      <span class="kpi-icon">{icon}</span>
    {/if}
    
    <h4 class="kpi-title">{title}</h4>
  </div>
  
  <div class="kpi-body">
    <div class="kpi-value">{value}</div>
  </div>
</div>