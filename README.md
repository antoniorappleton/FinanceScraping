# FinanceScraping 📈

Pipeline de scraping automatizado para dados de ativos globais (Ações & ETFs), com foco nos mercados europeus e americanos. O sistema sincroniza métricas financeiras e indicadores técnicos em tempo real diretamente para o Firestore.

## 🚀 Funcionalidades
- **Scraping Multi-Fonte**: Extração de dados confiável do Yahoo Finance (via yfinance & HTML), FT Markets, JustETF, Google Finance e Finviz.
- **Sistema Inteligente de Fallback**: Alterna automaticamente entre fornecedores se um falhar.
- **Indicadores Técnicos Automatizados**: Suporte nativo para **SMA50, SMA200 e RSI**. Se a fonte não fornecer, o sistema calcula-os automaticamente a partir do histórico de preços.
- **Propagação Automática para Portfólio**: Os dados atualizados em `acoesDividendos` são automaticamente propagados para a coleção `ativos`, mantendo o seu dashboard de portfólio sincronizado.
- **Foco Global**: Lógica especializada para Euronext, XETRA, mercado português (PSI) e mercado brasileiro (B3).
- **Lógica de Bootstrap Inteligente**: Deteta tickers com preços em falta ou `#N/A` e força uma atualização **FULL** imediata.

## ⚙️ Automação & Agendamento

O agendador local (`local_scheduler.py`) gere os ciclos de atualização sem intervenção:

| Modo | Frequência | Âmbito |
| :--- | :--- | :--- |
| **Priority Bootstrap** | Cada Execução | Tickers com `#N/A` recebem um Full Sync imediato. |
| **Fast Sync** | A cada 4 Horas* | Atualiza `valorStock`, `priceChange_1d` e `marketCap`. |
| **Full Sync** | Diário (20h) | Atualiza todos os indicadores (P/E, ROE, RSI, SMAs, Yield, Perf 1m/1y, etc.). |

*\*Intervalo configurável via linha de comando.*

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

### Execução Automatizada
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
- `local_scheduler.py`: Orquestrador de timing (bypass de limitações de cloud).
- `cron_scraper.py`: Lógica central de recolha e transformação.
- `scraper/`: Módulos especializados (Yahoo, FT, etc.) e o `FirebaseManager`.
- `tools/`: Scripts de manutenção e diagnóstico.

## 📝 Modelo de Dados & Integração
O sistema opera principalmente sobre a coleção `acoesDividendos`, mas integra-se com outras partes do ecossistema:

1. **acoesDividendos**: Master data dos ativos monitorizados.
2. **ativos**: O seu portfólio pessoal. O scraper atualiza automaticamente os preços e indicadores aqui sempre que encontra mudanças, garantindo que os KPIs de rentabilidade no dashboard estejam corretos.

**Campos Principais:**
`valorStock`, `priceChange_1d`, `yield`, `pe`, `rsi`, `sma50`, `sma200`, `marketCap`, `lastFullSync`.
