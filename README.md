# 🚀 Market Scraper Terminal & Automation

Este projecto é uma ferramenta poderosa de extracção e automação de dados financeiros. Permite tanto a recolha manual através de uma interface web como a sincronização automática diária com a cloud.

## ✨ Funcionalidades Principais

### 🖥️ Terminal de Pesquisa (Manual)

- **Pesquisa em lote**: Insira dezenas de tickers de uma vez (Finviz, Yahoo, Google Finance, Euronext).
- **Euronext Lisboa**: Dados precisos e diretos para o mercado português.
- **Exportação Direta**: Envia os dados para Google Sheets ou guarda localmente em JSON.

### 🤖 Automação Diária (Cloud Sync)

- **Sincronização Firestore**: O projecto lê automaticamente uma lista de tickers da sua base de dados Firebase e actualiza os indicadores de mercado todos os dias.
- **GitHub Actions**: Configurado para correr de forma totalmente autónoma (sem intervenção manual) todas as noites.
- **Multi-Source Failover**: Tenta obter dados de múltiplas fontes (Yahoo, Google, Finviz) para garantir que a sua base de dados está sempre actualizada.

---

## 🛠️ Configuração Inicial

Siga estes passos para preparar o ambiente em qualquer PC.

### 1. Pré-requisitos

- **Python 3.10+** instalado.
- **Git** (opcional, para clonar o repositório).

### 2. Instalação e Ambiente Virtual

No terminal (PowerShell ou CMD), execute:

```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
.\.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração do Ficheiro .env

Crie um ficheiro chamado `.env` na raiz do projeto (ou edite o existente) com o seguinte conteúdo:

```env
G_SHEETS_WEBHOOK_URL=SEU_URL_DO_APPS_SCRIPT
FIREBASE_SERVICE_ACCOUNT_JSON=C:\CAMINHO\PARA\O\SEU\FICHEIRO_FIREBASE.json
```

### 4. Abrir a Aplicação

```powershell
python app.py
```

Aceda a: **http://127.0.0.1:5000**

---

## 📊 Configuração de Integrações

### Google Sheets (Opcional)

Para exportar dados diretamente para uma folha de cálculo:

1. Na sua Google Sheet: **Extensões** -> **Apps Script**.
2. Copie o conteúdo de `docs/googlesheet_webhook.gs` para o editor.
3. **Implementar** -> **Nova implementação** -> Escolha **Aplicação Web**.
4. Configuração: Executar como **Eu**, Acesso: **Qualquer pessoa**.
5. Copie o URL gerado e coloque-o no seu `.env` em `G_SHEETS_WEBHOOK_URL`.

### Firebase (Opcional)

Para sincronizar dados com a cloud:

1. Aceda à [Consola do Firebase](https://console.firebase.google.com/).
2. Crie um projeto e adicione uma base de dados **Firestore**.
3. Vá a **Definições do Projeto** -> **Contas de Serviço**.
4. Clique em **Gerar nova chave privada** para descarregar o ficheiro JSON.
5. Guarde o JSON numa pasta segura e coloque o caminho completo no seu `.env` em `FIREBASE_SERVICE_ACCOUNT_JSON`.
6. **Para Automação (GitHub Actions)**: Copie o conteúdo deste ficheiro JSON e adicione-o como um **Secret** no GitHub (Settings -> Secrets and variables -> Actions) com o nome `FIREBASE_SERVICE_ACCOUNT`.

---

## 🚀 Como Usar

1. **Escolha a Fonte**: Recomenda-se `finviz` para dados americanos ou `euronext` para portugueses.
2. **Introduza os Tickers**: Cole a sua lista no campo de texto (um por linha ou separados por vírgula).
3. **Processar**: Clique em **"Processar tickers"**. O programa vai percorrer a lista um a um.
4. **Ver Resultados**: A tabela aparece automaticamente com os indicadores comparados.
5. **Exportar**:
   - Clique em **"Exportar JSON"** para guardar localmente.
   - Clique em **"Exportar Sheets"** para enviar para a sua folha de cálculo.

### 🇵🇹 Euronext (Ideal para Portugal)

A fonte `euronext` foi desenhada para o mercado português (Lisboa) e europeu:

- **Ticker Direto**: Não precisa de sufixo (ex: basta `EDP` ou `GALP`).
- **Mapeamento Automático**: O terminal pesquisa o ISIN e o mercado (ex: XLIS) automaticamente.
- **Métricas Locais**: Capitalização em Euros, Volume e variação real da bolsa de Lisboa.

---

## 📄 Notas & Licença

- **Delays**: A app aplica um delay de 1.5s entre tickers para evitar bloqueios.
- **Estrutura**: Os ficheiros raw ficam em `data/raw/`.
- **Licença**: MIT.
