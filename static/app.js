const sourceEl = document.getElementById("source");
const marketEl = document.getElementById("market");
const tickerEl = document.getElementById("ticker");
const searchBtn = document.getElementById("searchBtn");
const resultEl = document.getElementById("result");
const statusEl = document.getElementById("status");
const chips = document.querySelectorAll(".chip");

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
    resultEl.textContent = JSON.stringify(data, null, 2);

    if (!response.ok) {
      statusEl.textContent = "Pesquisa concluída com erro.";
      return;
    }

    statusEl.textContent = `Pesquisa concluída para ${ticker}.`;
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
