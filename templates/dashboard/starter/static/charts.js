// charts.js — vanilla JS, no deps. Renders the dashboard data.

(() => {
  const REFRESH = parseInt(
    document.getElementById('refresh-seconds').textContent || '30',
    10
  ) * 1000;
  const COLORS = {
    ink: '#111',
    accent: '#ff9500',
    grid: '#e5e5e0',
    bg: '#fafaf7',
  };

  async function fetchData() {
    const r = await fetch('/api/data');
    if (!r.ok) throw new Error('fetch failed');
    return r.json();
  }

  function renderSummary(d) {
    document.getElementById('source-name').textContent = d.source || '(none)';
    document.getElementById('card-rows').textContent =
      Array.isArray(d.rows) ? d.rows.length : 0;
    document.getElementById('card-columns').textContent =
      (d.columns || []).length;
    document.getElementById('card-updated').textContent =
      new Date().toLocaleTimeString();
  }

  function renderTable(d) {
    const head = document.querySelector('#data-table thead tr');
    const body = document.querySelector('#data-table tbody');
    head.innerHTML = '';
    body.innerHTML = '';
    if (!d.rows || !d.rows.length) {
      head.innerHTML = '<th>(no rows)</th>';
      return;
    }
    const cols = d.columns.length ? d.columns : Object.keys(d.rows[0]);
    cols.forEach((c) => {
      const th = document.createElement('th');
      th.textContent = c;
      head.appendChild(th);
    });
    d.rows.slice(0, 200).forEach((row) => {
      const tr = document.createElement('tr');
      cols.forEach((c) => {
        const td = document.createElement('td');
        td.textContent = row[c] ?? '';
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
  }

  function renderChart(d) {
    const canvas = document.getElementById('chart');
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    if (!d.rows || d.rows.length < 2) {
      ctx.fillStyle = COLORS.ink;
      ctx.font = '12px -apple-system, sans-serif';
      ctx.fillText('(not enough rows to chart)', 16, 24);
      return;
    }
    // Pick the first two columns: first as x, second numeric as y.
    const cols = d.columns.length ? d.columns : Object.keys(d.rows[0]);
    const xKey = cols[0];
    const yKey = cols.find((c) => c !== xKey) || cols[1];
    const xs = d.rows.map((r, i) => i);
    const ys = d.rows.map((r) => parseFloat(r[yKey]) || 0);
    const yMin = Math.min(...ys);
    const yMax = Math.max(...ys);
    const yRange = yMax - yMin || 1;

    // Grid
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = 30 + ((H - 60) / 4) * i;
      ctx.beginPath();
      ctx.moveTo(40, y);
      ctx.lineTo(W - 20, y);
      ctx.stroke();
    }

    // Line
    ctx.strokeStyle = COLORS.accent;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    xs.forEach((x, i) => {
      const cx = 40 + ((W - 60) / (xs.length - 1)) * x;
      const cy = H - 30 - ((ys[i] - yMin) / yRange) * (H - 60);
      if (i === 0) ctx.moveTo(cx, cy);
      else ctx.lineTo(cx, cy);
    });
    ctx.stroke();

    // Dots
    ctx.fillStyle = COLORS.accent;
    xs.forEach((x, i) => {
      const cx = 40 + ((W - 60) / (xs.length - 1)) * x;
      const cy = H - 30 - ((ys[i] - yMin) / yRange) * (H - 60);
      ctx.beginPath();
      ctx.arc(cx, cy, 2, 0, Math.PI * 2);
      ctx.fill();
    });

    // Labels
    ctx.fillStyle = COLORS.ink;
    ctx.font = '10px -apple-system, sans-serif';
    ctx.fillText(`${yKey}: ${yMin}–${yMax}`, 16, 18);
  }

  async function tick() {
    try {
      const d = await fetchData();
      renderSummary(d);
      renderChart(d);
      renderTable(d);
    } catch (e) {
      console.error('tick failed', e);
    }
  }

  tick();
  setInterval(tick, REFRESH);
})();
