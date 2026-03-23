// Portfolio Analysis JS
let holdingsChart;

async function loadPortfolioData(ticker) {
  try {
    const response = await fetch(`/api/analyze-etf?ticker=${ticker}`);
    if (!response.ok) throw new Error('API error');
    const data = await response.json();
    
    renderSignal(data);
    renderPerfTable(data.perf);
    renderRiskCards(data.risk);
    renderAlloc(data.algo);
    renderHoldingsChart(data.holdings);
    renderFundFacts(data.fund);
    renderRawMetrics(data.raw_metrics);
    
  } catch (error) {
    console.error('Error loading data:', error);
    document.getElementById('signal-badge').textContent = 'ERROR';
    document.getElementById('signal-badge').style.background = '#ef4444';
  }
}

function renderSignal(data) {
  const badge = document.getElementById('signal-badge');
  const display = document.getElementById('score-display');
  
  let color = '#10b981'; // green
  let signal = data.algo.signal;
  if (signal.includes('AVOID')) color = '#ef4444'; // red
  else if (signal === 'HOLD') color = '#f59e0b'; // amber
  
  badge.textContent = signal;
  badge.style.background = color;
  badge.style.color = 'white';
  
  display.innerHTML = `Score: ${data.algo.score} | Alloc: ${data.algo.alloc_pct} | Risk: ${data.risk.risk_level} | Trend: ${data.algo.trend}`;
}

function renderPerfTable(perf) {
  const tbody = document.querySelector('#perf-table tbody');
  tbody.innerHTML = '';
  
  const periods = [
    {name: '1 Month', val: perf['1m']},
    {name: '3 Months', val: perf['3m']},
    {name: '6 Months', val: perf['6m']},
    {name: '1 Year', val: perf['1y']},
    {name: 'Ann 3Y', val: perf.ann_3y},
    {name: 'Ann 5Y', val: perf.ann_5y}
  ];
  
  periods.forEach(p => {
    const row = tbody.insertRow();
    row.innerHTML = `<td>${p.name}</td><td style="color: ${p.val >= 0 ? '#10b981' : '#ef4444'}">${(p.val*100).toFixed(1)}%</td>`;
  });
}

function renderRiskCards(risk) {
  const container = document.getElementById('risk-cards');
  container.innerHTML = `
    <div class="metric-card"><strong>Vol 1Y</strong><span>${(risk.vol_1y*100).toFixed(1)}%</span></div>
    <div class="metric-card"><strong>Max DD 3Y</strong><span>${(risk.dd_3y*100).toFixed(1)}%</span></div>
    <div class="metric-card"><strong>Risk Score</strong><span>${risk.risk_score.toFixed(3)}</span></div>
    <div class="metric-card"><strong>Level</strong><span>${risk.risk_level}</span></div>
  `;
}

function renderAlloc(algo) {
  const badge = document.getElementById('alloc-badge');
  const warnings = document.getElementById('warnings');
  
  badge.textContent = algo.alloc_pct;
  badge.style.color = '#10b981';
  
  if (algo.warnings.length > 0) {
    warnings.innerHTML = algo.warnings.map(w => `<div>• ${w}</div>`).join('');
  } else {
    warnings.innerHTML = '<div style="color: #10b981;">Good diversification</div>';
  }
}

function renderHoldingsChart(holdings) {
  const ctx = document.getElementById('holdings-chart').getContext('2d');
  
  if (holdingsChart) holdingsChart.destroy();
  
  const labels = Object.keys(holdings);
  const values = Object.values(holdings);
  
  holdingsChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels.map(shortenLabel),
      datasets: [{ data: values, backgroundColor: ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#10b981','#f97316'] }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'right' } }
    }
  });
  
  // List top
  const list = document.getElementById('top-holdings-list');
  list.innerHTML = labels.slice(0,5).map((l,i) => 
    `<div style="display: flex; justify-content: space-between;"><span>${shortenLabel(l)}</span><span>${(values[i]*100).toFixed(1)}%</span></div>`
  ).join('');
}

function shortenLabel(label) {
  return label.replace(/_/g, ' ').replace(/^[a-z]/, c => c.toUpperCase()).slice(0,20);
}

function renderFundFacts(fund) {
  const container = document.getElementById('fund-facts');
  container.innerHTML = `
    <div class="metric-card"><strong>TER</strong><span>${fund.ter}</span></div>
    <div class="metric-card"><strong>AuM</strong><span>${fund.fund_size}</span></div>
    <div class="metric-card"><strong>Replication</strong><span>${fund.replication}</span></div>
  `;
}

function renderRawMetrics(metrics) {
  const container = document.getElementById('raw-metrics');
  container.innerHTML = JSON.stringify(metrics, null, 2);
}
