/**
 * Google Apps Script Webhook para o Market Scraper Terminal
 * 
 * Instruções:
 * 1. Na sua Google Sheet, vá a Extensões -> Apps Script.
 * 2. Apague qualquer código existente e cole este conteúdo.
 * 3. Clique em "Implementar" -> "Nova implementação".
 * 4. Tipo: "Aplicação Web".
 * 5. Descrição: "Market Scraper Webhook".
 * 6. Executar como: "Eu" (o seu e-mail).
 * 7. Quem tem acesso: "Qualquer pessoa" (isso é necessário para o Terminal conseguir enviar dados).
 * 8. Clique em "Implementar", autorize as permissões e copie o "URL da aplicação web".
 */

const TARGET_SHEET_NAME = "Historico_Terminal"; // Nome da aba onde os dados serão guardados

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(TARGET_SHEET_NAME);
    
    // Cria a aba se não existir
    if (!sheet) {
      sheet = ss.insertSheet(TARGET_SHEET_NAME);
    }
    
    const columns = data.columns;
    const rows = data.rows;
    
    if (!columns || !rows || rows.length === 0) {
      return ContentService.createTextOutput(JSON.stringify({
        "status": "error",
        "message": "Dados inválidos ou vazios"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Adiciona o cabeçalho se a aba estiver vazia
    if (sheet.getLastRow() === 0) {
      // Adiciona "Timestamp_Export" como primeira coluna extra
      const header = ["Timestamp_Export", ...columns];
      sheet.appendRow(header);
      sheet.getRange(1, 1, 1, header.length).setFontWeight("bold").setBackground("#f3f3f3");
    }
    
    const timestamp = new Date().toISOString();
    
    // Adiciona cada linha
    rows.forEach(row => {
      const rowData = [timestamp];
      columns.forEach(col => {
        rowData.push(row[col] || "");
      });
      sheet.appendRow(rowData);
    });
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "rows_added": rows.length
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
