# FinanceScraping 📈

Pipeline de scraping automatizado para dados de ativos globais (Ações & ETFs), com foco nos mercados europeus e americanos. O sistema sincroniza métricas financeiras e indicadores técnicos diretamente para o Firestore.

## 🚀 Funcionalidades
- **Scraping Multi-Fonte**: Extração de dados confiável do Yahoo Finance (via yfinance & HTML), FT Markets, JustETF, Google Finance e Finviz.
- **Sistema Inteligente de Fallback**: Alterna automaticamente entre fornecedores se um falhar.
- **Indicadores Técnicos Automatizados**: Suporte nativo para **SMA50, SMA200 e RSI**. Se a fonte não fornecer, o sistema calcula-os automaticamente a partir do histórico de preços.
- **Propagação Automática para Portfólio**: Os dados atualizados em `acoesDividendos` são automaticamente propagados para a coleção `ativos`, mantendo o seu dashboard de portfólio sincronizado.
- **Proteção de Dados**: Campos com valor `None` nunca sobrescrevem dados válidos existentes no Firestore — valores como SMAs calculados manualmente ou por fallback permanecem intactos até serem atualizados por novos dados válidos.
- **Foco Global**: Lógica especializada para Euronext, XETRA, mercado português (PSI) e mercado brasileiro (B3).
- **Lógica de Bootstrap Inteligente**: Deteta tickers com preços em falta ou `#N/A` e força uma atualização **FULL** imediata.

---

## ⚙️ Automação & Agendamento (GitHub Actions)

O sistema opera com **2 workflows** automatizados no GitHub Actions, otimizados para ficar dentro do limite gratuito (~155 runs/mês):

| Modo | Workflow | Cron (UTC) | Frequência | Âmbito |
| :--- | :--- | :--- | :--- | :--- |
| **Fast Sync** | `fast_scrape.yml` | `15 */6 * * *` | A cada **6 horas** | Preço, variação diária, market cap |
| **Full Sync** | `full_scrape.yml` | `30 2 * * *` | **Diário** às 02:30 UTC | Todos os indicadores (ver tabela abaixo) |
| **Bootstrap** | Automático | — | Cada execução | Tickers com `#N/A` recebem Full Sync imediato |

### 🕐 Próximas Execuções Agendadas

**Fast Sync** (a cada 6h, minuto :15):
| # | Data & Hora (UTC) | Hora Lisboa |
|---|---|---|
| 1 | 2026-04-29 00:15 | 01:15 |
| 2 | 2026-04-29 06:15 | 07:15 |
| 3 | 2026-04-29 12:15 | 13:15 |
| 4 | 2026-04-29 18:15 | 19:15 |

**Full Sync** (diário às 02:30 UTC):
| # | Data & Hora (UTC) | Hora Lisboa |
|---|---|---|
| 1 | 2026-04-29 02:30 | 03:30 |
| 2 | 2026-04-30 02:30 | 03:30 |
| 3 | 2026-05-01 02:30 | 03:30 |

### Proteções dos Workflows
- **Concurrency groups**: Impede execuções sobrepostas do mesmo tipo.
- **Timeout**: 15 min (fast) / 30 min (full) — mata jobs pendurados.
- **Pip cache**: Acelera instalação de dependências.
- **Rate limiting inteligente**: Delay de 3s com jitter entre tickers + backoff exponencial em erros 429.

---

## 📊 Indicadores Tratados

### Coleção `acoesDividendos`

#### Fast Sync (a cada 6h)

| Campo Firestore | Descrição | Fontes |
| :--- | :--- | :--- |
| `valorStock` | Preço atual do ativo | Yahoo, FT, Google, Finviz |
| `priceChange_1d` | Variação diária (%) | Yahoo, FT, Google, Finviz |
| `marketCap` | Capitalização de mercado | Yahoo, FT, Google, Finviz |
| `nome` | Nome da empresa/fundo | Todas |
| `source_used` | Fonte utilizada | — |

#### Full Sync (diário)

Inclui todos os campos do Fast Sync, mais:

| Campo Firestore | Categoria | Descrição | Fontes |
| :--- | :--- | :--- | :--- |
| **Performance** | | | |
| `priceChange_1w` | Tendência | Variação semanal (%) | Yahoo, Finviz |
| `priceChange_1m` | Tendência | Variação mensal (%) | Yahoo, Finviz |
| `priceChange_1y` | Tendência | Variação anual (%) | Yahoo, Finviz |
| **Avaliação** | | | |
| `pe` | Valuation | Price/Earnings ratio (TTM) | Yahoo, FT, Finviz |
| `yield` | Dividendos | Dividend Yield (%) | Yahoo, FT, JustETF |
| `ev_ebitda` | Valuation | Enterprise Value / EBITDA | Finviz |
| `ebitda` | Financeiro | EBITDA | Finviz |
| **Rentabilidade** | | | |
| `roa` | Eficiência | Return on Assets (%) | Finviz |
| `roe` | Eficiência | Return on Equity (%) | Finviz |
| `roi` | Eficiência | Return on Investment (%) | Finviz |
| `roic` | Eficiência | Return on Invested Capital (%) | Finviz |
| **Indicadores Técnicos** | | | |
| `rsi` | Momentum | Relative Strength Index (14) | Yahoo, Finviz |
| `sma20` | Média Móvel | Simple Moving Average 20 dias | Yahoo (cálculo) |
| `sma50` | Média Móvel | Simple Moving Average 50 dias | Yahoo, Finviz (cálculo) |
| `sma100` | Média Móvel | Simple Moving Average 100 dias | Yahoo (cálculo) |
| `sma200` | Média Móvel | Simple Moving Average 200 dias | Yahoo, Finviz (cálculo) |
| `sma_vol20` | Volume | SMA de Volume 20 dias | Yahoo (cálculo) |
| **Sinais** | | | |
| `above_sma50` | Sinal | Preço acima da SMA50? (bool) | Calculado |
| `above_sma200` | Sinal | Preço acima da SMA200? (bool) | Calculado |
| `golden_cross` | Sinal | SMA50 > SMA200? (bool) | Calculado |
| **Metadados** | | | |
| `lastFullSync` | Timestamp | Data/hora do último Full Sync | — |
| `updatedAt` | Timestamp | Último update (server timestamp) | — |

### Fluxo de Dados & Propagação

1. **Master Collection (`acoesDividendos`)**: É o destino principal e exaustivo. Todos os 25+ indicadores descritos acima são guardados aqui.
2. **Sync Automático (`ativos`)**: Sempre que a master é atualizada, o sistema propaga automaticamente apenas os campos essenciais para a coleção de portfólio (ativos), garantindo que o dashboard esteja sempre sincronizado com os dados mais recentes:

   `valorStock`, `sma50`, `sma200`, `priceChange_1d`, `rsi`, `yield`, `pe`, `roe`, `roa`

---

## 🌐 Fontes por Mercado

| Mercado | Prioridade de Fontes |
| :--- | :--- |
| 🇪🇺 Europa (XETRA, Euronext, JustETF) | FT Markets → JustETF → Yahoo → Google Finance |
| 🇵🇹 Portugal (PSI) | Yahoo → Google Finance → FT Markets |
| 🇧🇷 Brasil (B3) | Yahoo |
| 🇺🇸 EUA / Global | Yahoo → FT Markets → Google Finance → Finviz |

---

## 🛠️ Configuração

### Pré-requisitos
- Python 3.8+
- [Projeto Firebase](https://console.firebase.google.com/) com JSON de Service Account.

### Instalação
1. Clone o repositório.
2. Configure o ambiente virtual e instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure o ficheiro `.env`:
   ```env
   FIREBASE_SERVICE_ACCOUNT_JSON=C:\caminho\para\o\seu\firebase-key.json
   ```

## 📖 Utilização

### Execução Automatizada (Local)
```bash
python local_scheduler.py --interval-minutes 240
```

### Execução Manual
```bash
# Atualizar apenas o preço
python cron_scraper.py --mode fast

# Atualizar todas as métricas e indicadores técnicos
python cron_scraper.py --mode full
```

## 📂 Estrutura do Projeto
- `local_scheduler.py`: Orquestrador de timing local (alternativa ao GitHub Actions).
- `cron_scraper.py`: Lógica central de recolha e transformação.
- `scraper/`: Módulos especializados (Yahoo, FT, etc.) e o `FirebaseManager`.
- `.github/workflows/`: Automação via GitHub Actions (fast + full sync).
- `tools/`: Scripts de manutenção e diagnóstico.
- `scratch/`: Scripts auxiliares (ex: atualização manual de SMAs).
