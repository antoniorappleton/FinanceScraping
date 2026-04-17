# FinanceScraping 📈

Pipeline de scraping automatizado para dados de ativos globais (Ações & ETFs), com foco nos mercados europeus. O sistema sincroniza métricas financeiras em tempo real diretamente para o Firestore.

## 🚀 Funcionalidades
- **Scraping Multi-Fonte**: Extração de dados confiável do Yahoo Finance, FT Markets, JustETF, Google Finance e Finviz.
- **Sistema Inteligente de Fallback**: Alterna automaticamente entre fornecedores se um falhar ou retornar dados inválidos.
- **Foco em Ativos Europeus**: Lógica especializada para Euronext, XETRA e mercado português.
- **Lógica de Bootstrap Inteligente**: Deteta automaticamente tickers com preços em falta ou inválidos (`#N/A`) e força a atualização imediata antes de seguir os ciclos normais.
- **Frequência Dinâmica**: Atualizações de preço de alta frequência vs. verificações semanais completas de saúde financeira.

## ⚙️ Automação & Agendamento

O projeto inclui um agendador local robusco (`local_scheduler.py`) desenhado para manter a base de dados atualizada sem intervenção manual:

| Modo | Frequência | Âmbito |
| :--- | :--- | :--- |
| **Priority Bootstrap** | Cada Execução | Tickers com `#N/A` ou sem `valorStock` são atualizados imediatamente. |
| **Fast Sync** | A cada 4 Horas* | Atualiza `valorStock`, `priceChange_1d` e `marketCap`. |
| **Full Sync** | Semanal (Domingos) | Atualiza todos os indicadores (P/E, ROE, RSI, Yield, Performance 1m/1y, etc.). |

*\*Intervalo padrão, configurável via linha de comando.*

## 🛠️ Configuração

### Pré-requisitos
- Python 3.8+
- [Projeto Firebase](https://console.firebase.google.com/) com um JSON de Service Account.

### Instalação
1. Clone o repositório.
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure o ficheiro `.env`:
   ```env
   FIREBASE_SERVICE_ACCOUNT_JSON=C:\caminho\para\o\seu\firebase-key.json
   ```

## 📖 Utilização

### Execução Automatizada (Recomendado)
Execute o agendador local em background. Ele fará a gestão automática das frequências e modos.
```bash
python local_scheduler.py --interval-4h
```

### Execução Manual
Pode disparar manualmente modos de sincronização específicos usando o `cron_scraper.py`:
```bash
# Atualizar apenas o preço e info básica para todos os tickers
python cron_scraper.py --mode fast

# Atualizar todas as métricas financeiras (ideal para execuções semanais)
python cron_scraper.py --mode full
```

## 📂 Estrutura do Projeto
- `local_scheduler.py`: Serviço de background que orquestra o timing das sincronizações.
- `cron_scraper.py`: Lógica central de recolha de dados e atualização do Firestore.
- `scraper/`: Módulos especializados para cada fornecedor (Yahoo, FT, etc.).
- `tools/`: Scripts utilitários para manutenção da base de dados e diagnósticos.
- `app.py`: (Opcional) Interface web para análise de portfólio e visualização.

## 📝 Modelo de Dados & Gestão de Tickers
O sistema lê a partir da coleção `acoesDividendos` no Firestore.

**Para adicionar um novo ticker:**
1. Crie um documento com o Ticker como ID (ex: `AAPL` ou `XETR_VVMX`).
2. Defina o campo `mercado` (ex: `Portugal`, `US`, `Xetra`).
3. (Opcional) Defina o `valorStock` como `#N/A` se quiser que o scraper o priorize imediatamente.

**Para forçar uma atualização completa de um ticker:**
O agendador gere isto com base no timestamp `lastFullSync`, mas pode sempre correr `--mode full` manualmente.
