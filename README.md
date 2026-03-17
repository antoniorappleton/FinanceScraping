# FinanceScraping - Market Scraper Terminal App

[![Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-brightgreen?style=for-the-badge&logo=github)](https://antoniorappleton.github.io/FinanceScraping/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/Live_Demo-MIT-yellow.svg)](LICENSE)

## 📄 Descrição

**FinanceScraping** é uma aplicação web terminal para scraping de cotações financeiras de múltiplas fontes. Suporta scraping de **Finviz**, **Yahoo Finance** e **Google Finance**, com suporte a mercados **US**, **EU**, **PT** e **BR**.

Dados são salvos automaticamente em formato JSON na pasta `data/raw/`.

## ✨ Funcionalidades

- Interface web simples (Flask)
- Scrapers para:
  - [Finviz](https://finviz.com/)
  - [Yahoo Finance](https://finance.yahoo.com/)
  - [Google Finance](https://www.google.com/finance)
- Mercados suportados: 🇺🇸 US (Americano), 🇪🇺 EU (Europeu), 🇵🇹 PT (Português), 🇧🇷 BR (Brasileiro)
- API endpoint `/api/search` para buscas programáticas
- Salvamento automático de dados raw
- Estrutura modular com registry de scrapers

## 🌐 Live Demo

**Static demo** da interface (pesquisa simulada, dados demo). Funciona em **browser e telemóvel**!

[![Demo Screenshot](https://img.shields.io/badge/Teste_Móvel-Browser/Phone-green)](https://antoniorappleton.github.io/FinanceScraping/)

**App completa:** Execute localmente (`python app.py`).

## 📱 Demo UI

![Screenshot](screenshots/demo.png)
*(Adicione screenshot da interface aqui)*

## 🛠️ Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/antoniorappleton/FinanceScraping.git
   cd FinanceScraping
   ```

2. Crie um ambiente virtual:
   ```
   python -m venv venv
   # Windows:
   venv\\Scripts\\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. Instale dependências:
   ```
   pip install -r requirements.txt
   ```

4. Execute a aplicação:
   ```
   python app.py
   ```

5. Abra http://127.0.0.1:5000 no browser.

## 🚀 Uso

### Via Interface Web (Terminal de Lote)

1. **Selecionar Contexto**: 
   - Escolha a **Fonte** (atualmente `finviz` é a recomendada para a Fase 1).
   - Escolha o **Mercado** (ex: `US` para tickers americanos).

2. **Inserir Tickers**: 
   - No campo de texto grande, cole um ou vários tickers.
   - Pode inserir um por linha ou separados por vírgula (ex: `AAPL`, `MSFT`, `NVDA`).

3. **Processar**: 
   - Clique em **"Processar tickers"**.
   - A aplicação irá percorrer a lista sequencialmente com um pequeno delay (1.5s) para evitar bloqueios.

4. **Visualizar e Analisar**: 
   - Veja o resumo (sucessos/erros) no topo.
   - Analise os resultados na tabela comparativa (use o scroll horizontal se necessário).
   - Erros individuais aparecem numa secção separada sem interromper o lote.

5. **Guardar/Exportar**: 
   - Os dados são salvos automaticamente em `data/raw` como um ficheiro JSON único do lote.
   - Use o botão **"Exportar JSON"** para descarregar o resultado atual.

### Via API (Programático)

#### Batch Search
```
POST /api/search-batch
{
  "tickers": "AAPL, MSFT, NVDA",
  "source": "finviz",
  "market": "US"
}
```

#### Pesquisa Única
```
POST /api/search
{
  "ticker": "AAPL",
  "source": "yahoo",
  "market": "US"
}
```

## 📂 Estrutura do Projeto

```
market_scraper_terminal/
├── app.py                 # Aplicação Flask principal
├── requirements.txt       # Dependências
├── README.md             # Este ficheiro
├── .gitignore
├── data/
│   ├── raw/              # Dados JSON salvos
│   └── processed/
├── logs/                 # Logs da aplicação
├── scraper/              # Módulo de scrapers
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py       # Registro de scrapers
│   ├── finviz.py
│   ├── yahoo.py
│   └── google_finance.py
├── static/
│   ├── app.js
│   └── style.css
└── templates/
    └── index.html
```

## 🔧 Desenvolvimento

- **Adicionar novo scraper**: Crie classe herdando `BaseScraper`, registre em `registry.py`
- **Novos mercados**: Atualize `SUPPORTED_MARKETS` em `registry.py`
- **Dados processados**: Implemente processamento em `data/processed/`

## ⚠️ Avisos

- Scraping pode violar ToS das fontes. Uso educacional.
- Rate limiting não implementado (adicionar delays).
- Use proxies/VPN se necessário.

## 🤝 Contribuições

1. Fork o projeto
2. Crie branch `feat/nova-fonte`
3. Commit mudanças
4. Push e abra Pull Request

## 📄 Licença

MIT License - ver `LICENSE` (crie se necessário).

## 👨‍💻 Autor

[Antonio Appleton](https://github.com/antoniorappleton)

---

⭐ Star ⭐ e contribua!

