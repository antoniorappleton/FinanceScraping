const sourceEl = document.getElementById("source");
const marketEl = document.getElementById("market");
const tickerEl = document.getElementById("ticker");
const searchBtn = document.getElementById("searchBtn");
const resultEl = document.getElementById("result");
const statusEl = document.getElementById("status");
const chips = document.querySelectorAll(".chip");

let debounceTimer;
const DEBOUNCE_MS = 300;

// Search ticker suggestions
async function fetchSuggestions(query, source, market) {
  try {
    const response = await fetch("/api/search_ticker", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, source, market }),
    });
    const data = await response.json();
    return data.suggestions || [];
  } catch {
    return [];
  }
}

// Show suggestions dropdown
function showSuggestions(suggestions) {
  // Remove existing dropdown
  const existing = document.querySelector("#suggestions");
  if (existing) existing.remove();

  if (suggestions.length === 0) return;

  const dropdown = document.createElement("div");
  dropdown.id = "suggestions";
  dropdown.className = "suggestions-dropdown";
  suggestions.forEach((sug) => {
    const item = document.createElement("div");
    item.className = "suggestion-item";
    item.textContent = `${sug.ticker} - ${sug.name}`;
    item.onclick = () => {
      tickerEl.value = sug.ticker;
      dropdown.remove();
      searchTicker();
    };
    dropdown.appendChild(item);
  });
  tickerEl.parentNode.appendChild(dropdown);
}

async function searchTicker() {
  const ticker = tickerEl.value.trim().toUpperCase();
  const source = sourceEl.value;
  const market = marketEl.value;

  if (!ticker) {
    statusEl.textContent = "Introduz um ticker.";
    return;
  }

  statusEl.textContent = `A pesquisar ${ticker} em ${source} (${market})...`;
  resultEl.textContent = "A carregar...";

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ticker,
        source,
        market,
      }),
    });

    const data = await response.json();

    if (data.suggestions && data.suggestions.length > 0) {
      let msg = data.error ? `${data.error} Sugestões:\n` : "Sugestões:\n";
      data.suggestions.slice(0, 3).forEach((s) => {
        msg += `- ${s.ticker}: ${s.name}\n`;
      });
      statusEl.textContent = msg;
    } else {
      statusEl.textContent = data.error || `Pesquisa concluída para ${ticker}.`;
    }

    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    resultEl.textContent = JSON.stringify(
      {
        error: "Erro de comunicação com o backend.",
        details: String(error),
      },
      null,
      2,
    );
    statusEl.textContent = "Falha de comunicação.";
  }
}

// Debounced autocomplete
tickerEl.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  const query = tickerEl.value.trim();
  if (query.length < 2) return;

  debounceTimer = setTimeout(async () => {
    const suggestions = await fetchSuggestions(
      query,
      sourceEl.value,
      marketEl.value,
    );
    showSuggestions(suggestions);
  }, DEBOUNCE_MS);
});

searchBtn.addEventListener("click", searchTicker);
tickerEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    searchTicker();
  }
});

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    tickerEl.value = chip.dataset.ticker;
    searchTicker();
  });
});

// Hide suggestions on outside click
document.addEventListener("click", (e) => {
  if (!tickerEl.contains(e.target) && !e.target.matches("#suggestions *")) {
    const dropdown = document.querySelector("#suggestions");
    if (dropdown) dropdown.remove();
  }
});
