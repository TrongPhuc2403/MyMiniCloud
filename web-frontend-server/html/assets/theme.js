// Only the display preference is persisted; credentials never enter storage.
(() => {
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let preference;
  try { preference = localStorage.getItem('myminicloud-theme'); } catch { /* Storage may be blocked. */ }
  root.dataset.theme = preference === 'dark' || preference === 'light' ? preference : system.matches ? 'dark' : 'light';
  function updateLabel() {
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      const dark = root.dataset.theme === 'dark';
      button.setAttribute('aria-label', dark ? 'Chuyển sang Light Mode' : 'Chuyển sang Dark Mode');
      button.setAttribute('aria-pressed', String(dark));
      button.title = dark ? 'Light Mode' : 'Dark Mode';
    });
  }
  document.addEventListener('DOMContentLoaded', () => {
    updateLabel();
    document.querySelectorAll('[data-theme-toggle]').forEach(button => button.addEventListener('click', () => {
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      preference = root.dataset.theme;
      try { localStorage.setItem('myminicloud-theme', preference); } catch { /* Optional preference. */ }
      updateLabel();
    }));
  });
  system.addEventListener('change', event => {
    if (!preference) { root.dataset.theme = event.matches ? 'dark' : 'light'; updateLabel(); }
  });
})();
