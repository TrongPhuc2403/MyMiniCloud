'use strict';
(() => {
  const $ = selector => document.querySelector(selector);
  const pages = [...document.querySelectorAll('[data-page]')];
  const mobileButton = $('#mobile-menu');
  const sidebar = $('#sidebar');
  const mobileQuery = window.matchMedia('(max-width: 760px)');
  const pageTitles = {overview:'Overview',infrastructure:'Infrastructure',services:'Services','api-explorer':'API Explorer',database:'Database',authentication:'Authentication','object-storage':'Object Storage',dns:'DNS',monitoring:'Monitoring','load-balancer':'Load Balancer',documentation:'Documentation'};

  function closeMenu(restoreFocus = false) {
    document.body.classList.remove('menu-open');
    mobileButton.setAttribute('aria-expanded', 'false');
    mobileButton.setAttribute('aria-label', 'Mở menu');
    sidebar.inert = mobileQuery.matches;
    if (restoreFocus) mobileButton.focus();
  }
  function route(focus = false) {
    let id = location.hash.slice(1) || 'overview';
    if (id === 'main' && pages.some(page => page.hidden)) return;
    // Preserve the former landing-page anchor used by the existing articles.
    if (id === 'kham-pha') id = 'services';
    if (!Object.hasOwn(pageTitles, id)) id = 'overview';
    for (const page of pages) page.hidden = page.dataset.page !== id;
    document.querySelectorAll('[data-nav]').forEach(link => {
      if (link.dataset.nav === id) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    $('#current-page').textContent = pageTitles[id];
    document.title = pageTitles[id] + ' · MyMiniCloud';
    closeMenu();
    if (focus) { $('#main').focus({preventScroll:true}); window.scrollTo({top:0}); }
  }
  window.addEventListener('hashchange', () => route(true));
  route();
  $('#collapse-sidebar').addEventListener('click', event => {
    const collapsed = document.body.classList.toggle('collapsed');
    event.currentTarget.setAttribute('aria-expanded', String(!collapsed));
    event.currentTarget.setAttribute('aria-label', collapsed ? 'Mở rộng sidebar' : 'Thu gọn sidebar');
  });
  mobileButton.addEventListener('click', () => {
    const open = document.body.classList.toggle('menu-open');
    mobileButton.setAttribute('aria-expanded', String(open));
    mobileButton.setAttribute('aria-label', open ? 'Đóng menu' : 'Mở menu');
    sidebar.inert = !open;
    if (open) sidebar.querySelector('a').focus();
  });
  $('#menu-scrim').addEventListener('click', () => closeMenu(true));
  sidebar.addEventListener('click', event => {
    if (event.target.closest('a') && mobileQuery.matches) closeMenu(true);
  });
  mobileQuery.addEventListener('change', () => closeMenu());
  document.addEventListener('keydown', event => {
    if (!document.body.classList.contains('menu-open')) return;
    if (event.key === 'Escape') { closeMenu(true); return; }
    if (event.key === 'Tab') {
      const links = [...sidebar.querySelectorAll('a[href],button')].filter(el => el.getClientRects().length);
      const first = links[0], last = links[links.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });

  // Compose exposes these consoles over HTTP. Never assume HTTPS on their ports.
  // Explicit public URLs take priority for TLS/proxy deployments.
  const config = window.MMC_CONFIG || {};
  const ports = {keycloak:8081,minio:9001,prometheus:9090,grafana:3000,exporter:9100};
  function publicUrl(key) {
    const configured = config[key];
    if (configured) {
      try {
        const url = new URL(configured);
        if (['http:', 'https:'].includes(url.protocol) && !url.username && !url.password) return url.href;
      } catch { /* Invalid public URLs are not used. */ }
      return null;
    }
    // No speculative downgrade links from an HTTPS dashboard.
    if (location.protocol !== 'http:') return null;
    const url = new URL(location.origin);
    url.port = ports[key];
    url.pathname = key === 'keycloak' ? '/admin/' : key === 'prometheus' ? '/targets' : key === 'exporter' ? '/metrics' : '/';
    return url.href;
  }
  document.querySelectorAll('[data-console]').forEach(link => {
    const url = publicUrl(link.dataset.console);
    if (url) { link.href = url; link.title = 'Địa chỉ từ cấu hình; chưa kiểm tra khả dụng: ' + url; }
    else {
      const note = document.createElement('span');
      note.className = 'small';
      note.textContent = 'Cần cấu hình URL công khai cho ' + link.dataset.console + ' trong assets/config.js.';
      link.replaceWith(note);
    }
  });

  function safeBody(text, secret = '') {
    let redacted = secret ? text.split(secret).join('[REDACTED]') : text;
    try {
      const sensitive = /^(access_token|refresh_token|id_token|authorization|token|password|secret)$/i;
      return JSON.stringify(JSON.parse(redacted), (key, value) => sensitive.test(key) ? '[REDACTED]' : value, 2);
    } catch { return redacted; }
  }
  async function timedFetch(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(path, {...options, signal:controller.signal, cache:'no-store', redirect:'error'});
      // Keep timeout active while receiving the response body.
      const text = await response.text();
      return {response, text};
    } finally { clearTimeout(timer); }
  }
  function networkMessage(error) {
    return error.name === 'AbortError' ? 'Request quá thời gian chờ (12 giây).' : 'Không kết nối được. Kiểm tra Gateway, backend và địa chỉ truy cập.';
  }
  const backendStatus = $('#backend-status');
  async function checkBackend() {
    backendStatus.textContent = 'Backend · đang kiểm tra…';
    backendStatus.className = 'badge';
    try {
      const {response, text} = await timedFetch('/api/hello', {headers:{Accept:'application/json'}});
      const json = JSON.parse(text);
      if (!response.ok || typeof json.message !== 'string' || !response.headers.get('content-type')?.includes('application/json')) throw new Error('Unexpected backend response');
      backendStatus.textContent = 'Backend · connected';
      backendStatus.className = 'badge good';
      backendStatus.title = 'GET /api/hello · HTTP ' + response.status + ' · kiểm tra lúc ' + new Date().toLocaleTimeString('vi-VN');
    } catch {
      backendStatus.textContent = 'Backend · unavailable';
      backendStatus.className = 'badge bad';
      backendStatus.title = 'GET /api/hello chưa trả JSON thành công. Đây không phải trạng thái của toàn bộ hạ tầng.';
    }
  }
  checkBackend();
  // Recheck on return to the tab; no background token or metrics requests.
  document.addEventListener('visibilitychange', () => { if (!document.hidden) checkBackend(); });
  const endpoint = $('#endpoint');
  const token = $('#bearer-token');
  const output = $('#api-response');
  const responseStatus = $('#response-status');
  const copyButton = $('#copy-response');
  let copyText = '';
  endpoint.addEventListener('change', () => {
    $('#token-row').hidden = endpoint.value !== '/api/secure';
    token.value = '';
  });
  $('#api-form').addEventListener('submit', async event => {
    event.preventDefault();
    const path = endpoint.value;
    if (!['/api/hello', '/student/', '/api/secure'].includes(path)) return;
    const headers = {Accept:'application/json'};
    const secret = path === '/api/secure' ? token.value.trim().replace(/^Bearer\s+/i, '') : '';
    if (secret) headers.Authorization = 'Bearer ' + secret;
    const sendButton = $('#send-request');
    sendButton.disabled = true;
    endpoint.disabled = true;
    copyButton.disabled = true;
    copyText = '';
    responseStatus.textContent = 'Đang gửi GET ' + path + '…';
    output.textContent = 'Loading response…';
    output.setAttribute('aria-busy', 'true');
    const start = performance.now();
    try {
      const {response, text} = await timedFetch(path, {headers});
      const json = response.headers.get('content-type')?.includes('application/json');
      responseStatus.textContent = 'HTTP ' + response.status + ' ' + response.statusText + ' · ' + Math.round(performance.now() - start) + ' ms' + (response.ok ? '' : ' · Request không thành công') + (!json ? ' · Phản hồi không phải JSON; kiểm tra tuyến Gateway.' : '');
      copyText = text ? safeBody(text, secret) : '';
      output.textContent = copyText || 'Empty response · Server không trả nội dung.';
      copyButton.disabled = !copyText;
    } catch (error) {
      responseStatus.textContent = 'Request failed';
      output.textContent = networkMessage(error);
    } finally {
      sendButton.disabled = false;
      endpoint.disabled = false;
      output.setAttribute('aria-busy', 'false');
      // Shorten the token lifetime, including on failed requests.
      token.value = '';
    }
  });
  copyButton.addEventListener('click', async () => {
    if (!copyText) return;
    try {
      await navigator.clipboard.writeText(copyText);
      responseStatus.textContent += ' · Đã sao chép';
    } catch {
      responseStatus.textContent += ' · Trình duyệt không cho phép clipboard. Chọn và sao chép nội dung phản hồi thủ công.';
      const range = document.createRange();
      range.selectNodeContents(output);
      const selection = window.getSelection();
      selection.removeAllRanges(); selection.addRange(range);
      output.focus();
    }
  });
  $('#inspect-node').addEventListener('click', async event => {
    const button = event.currentTarget;
    const result = $('#node-result');
    button.disabled = true;
    result.textContent = 'Đang gửi GET /…';
    try {
      const {response} = await timedFetch('/?inspect=' + Date.now(), {headers:{Accept:'text/html'}});
      const upstream = response.headers.get('X-Upstream-Addr');
      const balancer = response.headers.get('X-Load-Balancer');
      result.textContent = !response.ok ? 'HTTP ' + response.status + ' · Không đọc được request thành công.' : upstream && balancer ? 'HTTP ' + response.status + ' · X-Upstream-Addr: ' + upstream + ' · X-Load-Balancer: ' + balancer : 'HTTP ' + response.status + ' · Không có header cân bằng tải. Hãy truy cập qua Nginx Gateway cổng 80.';
    } catch (error) { result.textContent = networkMessage(error); }
    finally { button.disabled = false; }
  });
  // Clear secrets when leaving or putting this document into the back/forward cache.
  window.addEventListener('pagehide', () => { token.value = ''; });
})();
