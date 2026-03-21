const tickersEl = document.getElementById("tickers");
const batchSearchBtn = document.getElementById("batchSearchBtn");
const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary");
const errorListEl = document.getElementById("errorList");
const tableHeaderEl = document.getElementById("tableHeader");
const tableBodyEl = document.getElementById("tableBody");
const statusSection = document.getElementById("statusSection");
const errorSection = document.getElementById("errorSection");
const resultsSection = document.getElementById("resultsSection");
const exportJsonBtn = document.getElementById("exportJsonBtn");
const exportSheetsBtn = document.getElementById("exportSheetsBtn");
const syncFirebaseBtn = document.getElementById("syncFirebaseBtn");
const exportStatus = document.getElementById("exportStatus");

let lastBatchData = null;

function checkElements() {
  if (!tickersEl || !batchSearchBtn || !statusEl) {
    console.error("Required DOM elements not found");
    return false;
  }
  return true;
}

async function processBatch() {
  if (!checkElements()) return;

  const tickers = tickersEl.value.trim();

  if (!tickers) {
    alert("Por favor, introduz pelo menos um ticker.");
    return;
  }

  // Reset UI
  statusSection.style.display = "block";
  errorSection.style.display = "none";
  resultsSection.style.display = "none";
  statusEl.textContent = "🔍 Detetando ativos e mercados... Scraping multi-fonte automático!";
  summaryEl.innerHTML = "";
  errorListEl.innerHTML = "";
  batchSearchBtn.disabled = true;

  try {
    const response = await fetch("/api/search-batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tickers }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Erro no servidor");
    }

    const data = await response.json();
    lastBatchData = data;
    renderBatchResult(data);
  } catch (error) {
    statusEl.innerHTML = `<span class="error-text">Erro: ${error.message}</span>`;
  } finally {
    batchSearchBtn.disabled = false;
  }
}

function renderBatchResult(data) {
  statusEl.textContent = "Processamento concluído.";

  // Render Summary
  summaryEl.innerHTML = `
    <div class="stat">
      <span class="stat-label">Total Pedidos</span>
      <span class="stat-value">${data.total_requested}</span>
    </div>
    <div class="stat">
      <span class="stat-label">Sucesso</span>
      <span class="stat-value success">${data.total_success}</span>
    </div>
    <div class="stat">
      <span class="stat-label">Erros</span>
      <span class="stat-value ${data.total_errors > 0 ? 'error' : ''}">${data.total_errors}</span>
    </div>
  `;

  // Render Errors
  if (data.errors && data.errors.length > 0) {
    errorSection.style.display = "block";
    errorListEl.innerHTML = "";
    data.errors.forEach(err => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${err.ticker}:</strong> ${err.error}`;
      errorListEl.appendChild(li);
    });
  }

  // Render Table
  if (data.rows && data.rows.length > 0) {
    resultsSection.style.display = "block";

    // Header
    tableHeaderEl.innerHTML = "";
    data.columns.forEach(col => {
      const th = document.createElement("th");
      th.textContent = col;
      tableHeaderEl.appendChild(th);
    });

    // Body
    tableBodyEl.innerHTML = "";
    data.rows.forEach(row => {
      const tr = document.createElement("tr");
      data.columns.forEach(col => {
        const td = document.createElement("td");
        let val = row[col] || "-";

        // Special formatting for URL
        if (col === 'url' && val !== '-') {
            td.innerHTML = `<a href="${val}" target="_blank" rel="noopener">Link</a>`;
        } else {
            td.textContent = val;
        }
        tr.appendChild(td);
      });
      tableBodyEl.appendChild(tr);
    });
  }
}

// Event Listeners
if (batchSearchBtn) {
  batchSearchBtn.addEventListener("click", processBatch);
}

// Quick examples logic
document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    if (tickersEl) {
      tickersEl.value = chip.dataset.ticker.replace(/, /g, '\n');
    }
  });
});

// Export JSON
if (exportJsonBtn) {
  exportJsonBtn.addEventListener("click", () => {
    if (!lastBatchData) {
      alert("No data to export. Run a search first.");
      return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(lastBatchData, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `batch_export_${new Date().getTime()}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  });
}

// Export Sheets
if (exportSheetsBtn && exportStatus) {
  exportSheetsBtn.addEventListener("click", async () => {
    if (!lastBatchData) {
      alert("No data to export. Run a search first.");
      return;
    }

    exportSheetsBtn.disabled = true;
    exportSheetsBtn.textContent = 'Enviando...';
    exportStatus.style.display = 'block';
    exportStatus.innerHTML = '<span style="color: #94a3b8;">Enviando dados para a Google Sheet...</span>';

    try {
      const response = await fetch('/api/export-sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lastBatchData)
      });

      const result = await response.json();

      if (response.ok) {
        exportStatus.innerHTML = `<span style="color: #10b981;">✓ Sucesso! Linhas adicionadas à Sheet.</span>`;
      } else {
        const errorMsg = result.details ? `${result.error} (${result.details})` : (result.error || 'Falha na exportação');
        exportStatus.innerHTML = `<span style="color: #f43f5e;">✕ Erro: ${errorMsg}</span>`;
      }
    } catch (error) {
      exportStatus.innerHTML = `<span style="color: #f43f5e;">✕ Erro de conexão: ${error.message}</span>`;
    } finally {
      exportSheetsBtn.disabled = false;
      exportSheetsBtn.textContent = 'Exportar Sheets';
      setTimeout(() => { exportStatus.style.display = 'none'; }, 5000);
    }
  });
}

// Sync Firebase
if (syncFirebaseBtn && exportStatus) {
  syncFirebaseBtn.addEventListener("click", async () => {
    if (!lastBatchData) {
      alert("No data to sync. Run a search first.");
      return;
    }

    syncFirebaseBtn.disabled = true;
    syncFirebaseBtn.textContent = 'Sincronizando...';
    exportStatus.style.display = 'block';
    exportStatus.innerHTML = '<span style="color: #94a3b8;">Sincronizando dados com o Firebase...</span>';

    try {
      const response = await fetch('/api/sync-firebase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lastBatchData)
      });

      const result = await response.json();

      if (response.ok) {
        exportStatus.innerHTML = `<span style="color: #fbbf24;">✓ Sucesso! Batch guardado no Firestore.</span>`;
      } else {
        exportStatus.innerHTML = `<span style="color: #f43f5e;">✕ Erro: ${result.error || 'Falha na sincronização'}</span>`;
      }
    } catch (error) {
      exportStatus.innerHTML = `<span style="color: #f43f5e;">✕ Erro de conexão: ${error.message}</span>`;
    } finally {
      syncFirebaseBtn.disabled = false;
      syncFirebaseBtn.textContent = 'Sincronizar Cloud';
      setTimeout(() => { exportStatus.style.display = 'none'; }, 5000);
    }
  });
}

