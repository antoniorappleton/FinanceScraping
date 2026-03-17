# 🚀 Market Scraper Terminal

Aplicação local para recolha massiva de dados financeiros e exportação direta para **Google Sheets**.

## ✨ O que faz?
- **Pesquisa em lote**: Insira dezenas de tickers de uma vez (Finviz, Yahoo, Google Finance).
- **Dados Limpos**: Normaliza e organiza automaticamente os indicadores financeiros.
- **Exportação Direta**: Envia a tabela resultante para a sua Google Sheet com um clique.
- **Histórico**: Guarda cópias locais em JSON de cada extração.

---

## 🛠️ Como Começar

### 1. Instalar (Windows)
```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Abrir a Aplicação
```powershell
.\.venv\Scripts\python app.py
```
Depois aceda a: **http://127.0.0.1:5000**

---

## 🚀 Como Usar

1. **Escolha a Fonte**: Recomenda-se `finviz` para dados americanos.
2. **Introduza os Tickers**: Cole a sua lista no campo de texto (um por linha ou separados por vírgula).
3. **Processar**: Clique em **"Processar tickers"**. O programa vai percorrer a lista um a um.
4. **Ver Resultados**: A tabela aparece automaticamente com os indicadores comparados.
5. **Exportar**:
   - Clique em **"Exportar JSON"** para guardar localmente.
   - Clique em **"Exportar Sheets"** para enviar para a sua folha de cálculo.

---

## 📊 Configurar Google Sheets (Opcional)

Para enviar dados para a sua própria Sheet:
1. Abra a sua Google Sheet -> **Extensões** -> **Apps Script**.
2. Cole o código que está em `docs/googlesheet_webhook.gs`.
3. Clique em **Implementar** -> **Nova implementação** -> **Aplicação Web**.
4. Configure: Executar como **Eu**, Acesso: **Qualquer pessoa**.
5. Copie o URL gerado e coloque-o no seu ficheiro `.env`:
   `G_SHEETS_WEBHOOK_URL=SEU_URL_AQUI`

---

---

## 📄 Notas & Licença
- **Delays**: A app aplica um delay de 1.5s entre tickers para evitar bloqueios.
- **Estrutura**: Os ficheiros raw ficam em `data/raw/`.
- **Licença**: MIT.

**Autor**: [Antonio Appleton](https://github.com/antoniorappleton)

