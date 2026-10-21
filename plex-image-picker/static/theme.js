(function() {
  const html = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const stored = localStorage.getItem('theme');
  const mq = window.matchMedia('(prefers-color-scheme: dark)');

  function apply(theme) {
    html.setAttribute('data-bs-theme', theme);
    toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
  }

  apply(stored || (mq.matches ? 'dark' : 'light'));

  toggle.addEventListener('click', () => {
    const next = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', next);
    apply(next);
  });
})();
