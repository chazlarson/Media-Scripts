(function() {
  const selector = document.getElementById('theme-selector');
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }
  selector.addEventListener('change', () => applyTheme(selector.value));
  if (selector.value === 'auto') {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    mq.addEventListener('change', e => applyTheme(mq.matches ? 'dark' : 'light'));
    applyTheme(mq.matches ? 'dark' : 'light');
  } else {
    applyTheme(selector.value);
  }
})();