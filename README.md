# 🚀 Market Scraper Terminal & Automation

Este projeto é uma ferramenta avançada de extração, análise e automação de dados financeiros. Integra múltiplas fontes globais para fornecer uma visão 360º de ações, ETFs e Criptomoedas, com sincronização nativa para **Firebase Firestore**.

## ✨ Funcionalidades Principais

*   **Scraping Inteligente Multi-Fonte**: Combina dados do **Yahoo Finance**, **Google Finance**, **JustETF** e **Financial Times** para garantir precisão e resiliência a bloqueios.
*   **Mapeamento Automático de Mercados**: Identifica automaticamente se um ativo pertence ao mercado **USA**, **Europa (Xetra/Euronext)**, **Portugal** ou **Brasil**.
*   **Sincronização com Firebase**: Atualiza automaticamente a coleção `acoesDividendos` no Firestore com métricas em tempo real.
*   **Dashboard Web**: Interface Flask para visualizar logs, gerir a fila de processamento e monitorizar o estado das atualizações.
*   **GitHub Actions Ready**: Configurado para execuções agendadas na cloud (ex: a cada 4 horas).

---

## 🛠️ Instalação e Configuração

### 1. Preparar o Ambiente
```powershell
# Criar e ativar ambiente virtual
python -m venv .venv
.\.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração de Credenciais
Crie um ficheiro `.env` na raiz do projeto com os seguintes campos:
```env
FIREBASE_SERVICE_ACCOUNT_JSON=C:\caminho\para\seu-firebase-key.json
G_SHEETS_WEBHOOK_URL=https://script.google.com/macros/s/... (Opcional)
```

---

## 🚀 Como Executar

### Terminal (Automação)
O script `cron_scraper.py` é o motor principal. Aceita dois modos:

*   **Modo Rápido (Fast)**: Atualiza apenas Preço, Variação e Market Cap.
    ```powershell
    python cron_scraper.py --mode fast
    ```
*   **Modo Completo (Full)**: Sincroniza todos os indicadores fundamentais e técnicos (+30 métricas).
    ```powershell
    python cron_scraper.py --mode full
    ```

### Interface Web (Gestão)
Para abrir o painel de controlo:
```powershell
python app.py
```
Aceda a: **http://127.0.0.1:5000**

---

## 🔍 Configuração de Tickers e Mercados

O sistema deteta o mercado automaticamente através do campo `mercado` no seu banco de dados ou pelo formato do ticker:

| Mercado | Exemplo de Ticker | Notas |
| :--- | :--- | :--- |
| **Portugal** | `BCP`, `EDPR.LS` | Euronext Lisbon |
| **USA** | `AAPL`, `MSFT` | Nasdaq / NYSE |
| **Europa / ETFs** | `EXSA`, `EUNN`, `QDVE.DE` | Pesquisa no JustETF e Xetra |
| **Brasil** | `PETR4.SA` | B3 |
| **Global/Cripto** | `BTC-USD` | Yahoo Finance |

---

## 📁 Estrutura do Projeto

*   `cron_scraper.py`: O script principal de execução agendada.
*   `app.py`: Servidor Flask para a interface visual.
*   `scraper/`: Contém os módulos individuais para cada fonte de dados.
*   `scripts/`: Ferramentas secundárias para manutenção e reparação de dados.
*   `static/` & `templates/`: Ficheiros da interface web.

---
*MIT License © 2026*
