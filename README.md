# 🚀 Market Scraper Terminal & Automation

Este projeto é uma ferramenta avançada de extração, análise e automação de dados financeiros. Integra múltiplas fontes globais para fornecer uma visão 360º de ações, ETFs e Criptomoedas, com sincronização nativa para Firebase e Google Sheets.

## ✨ Funcionalidades Principais

### 🧠 Scraping Inteligente Automático
- **Motores de Decisão**: O sistema identifica automaticamente o tipo de ativo e o mercado (**US**, **Europa**, **Portugal**, **Brasil**, **Global**) a partir do formato do ticker.
- **Ecossistema Multi-Fonte**: Combina dados de fontes líderes para máxima precisão:
  - **Ações Portugal (PSI)**: Euronext (Live) + Yahoo Finance + Google Finance.
  - **Ações US (SP500/Nasdaq)**: Finviz + Yahoo Finance + Google Finance.
  - **ETFs Europeus**: JustETF (Específico) + Yahoo Finance.
  - **Criptomoedas**: Yahoo Finance (Dados em tempo real).
- **Consolidação de Indicadores**: Une dados fundamentais e técnicos num único registo.

### 🤖 Automação de Sincronização (Cloud Sync)
Otimizado para **GitHub Actions** ou execução local, utiliza uma estratégia de duas camadas:

1.  **Sincronização Rápida (Fast Sync)**:
    - **Frequência**: A cada 4 horas.
    - **Métricas**: Preço atual (`valorStock`), variação diária (`priceChange_1d`) e Capitalização.
2.  **Sincronização Completa (Full Sync)**:
    - **Frequência**: Diária ou Semanal.
    - **Métricas**: Todos os +30 indicadores financeiros (ROE, ROA, RSI, P/E, EV/EBITDA, etc.).

---

## 📊 Estrutura de Dados (`acoesDividendos`)

Cada ticker sincronizado no Firestore contém os seguintes campos normalizados:

| Categoria | Campos |
| :--- | :--- |
| **Preço & Performance** | `valorStock`, `priceChange_1d`, `priceChange_1w`, `priceChange_1m`, `priceChange_1y`, `perf_half_y`, `perf_quarter`, `target_price`, `volatility` |
| **Fundamentais** | `pe` (P/E Ratio), `pb` (P/B), `ebitda`, `ev_ebitda`, `enterprise_value`, `marketCap`, `eps_next_q`, `eps_next_y`, `eps_this_y` |
| **Dividendos** | `yield`, `dividendValue`, `dividend_est`, `dividend_ex_date`, `dividend_gr_3_5y` |
| **Rentabilidade** | `roe` (Return on Equity), `roa` (Return on Assets), `roic` (Return on Invested Capital), `roi` |
| **Análise Técnica** | `rsi` (Relative Strength Index - 14p), `sma50`, `sma200` |
| **Metadados** | `nome`, `ticker`, `mercado`, `source_used`, `ultimaAtu` |

---

## 🛠️ Guia de Execução

### Comandos Úteis

| Objetivo | Comando | Tempo Estimado |
| :--- | :--- | :--- |
| **Atualização Rápida** | `python cron_scraper.py --mode fast` | ~3 a 5 min (100 tickers) |
| **Atualização Completa** | `python cron_scraper.py --mode full` | **~20 a 35 min** (100 tickers)* |

*\*O tempo varia conforme o "Rate Limit" das fontes. O sistema inclui delays de segurança para evitar bloqueios.*

### Configuração de Tickers por Mercado
O sistema reconhece automaticamente os mercados:
- `ELI:BCP` ou `BCP.LS` → **Portugal** (Euronext Lisbon)
- `AAPL` ou `MSFT` → **US** (Nasdaq/NYSE)
- `EPA:CS` ou `CS.PA` → **França** (Euronext Paris)
- `VUAA.DE` → **Alemanha** (XETRA)

---

## ⚙️ Instalação e Configuração

### 1. Ambiente Virtual e Dependências
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuração do `.env`
Crie um ficheiro `.env` na raiz:
```env
G_SHEETS_WEBHOOK_URL=https://script.google.com/... (Opcional)
FIREBASE_SERVICE_ACCOUNT_JSON=C:\caminho\para\seu-firebase-key.json
```

### 3. Interface Web
Para gestão manual e visualização:
```powershell
python app.py
```
Aceda a: **http://127.0.0.1:5000**

---

## 📄 Notas Técnicas
- **Rate Limiting**: O Yahoo Finance pode bloquear o acesso se houver pedidos excessivos. O script possui lógica de retry e fallback automático para o Google Finance (via Euronext ELI).
- **RSI**: Calculado logicamente a partir do histórico de 30 dias para garantir precisão técnica.
- **Estrutura**: Ficheiros temporários de scraping são armazenados em `data/raw/` para auditoria.

---
*MIT License © 2026*
