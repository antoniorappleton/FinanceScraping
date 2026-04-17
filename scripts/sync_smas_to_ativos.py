import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

def sync_smas_to_ativos():
    load_dotenv()
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not cred_path:
        print("No cred path in .env")
        return

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    print("Sincronizando SMAs de 'acoesDividendos' para 'ativos'...")
    
    # 1. Obter todos os dados de acoesDividendos (para termos os SMAs em cache)
    market_data = {}
    market_docs = db.collection("acoesDividendos").stream()
    for doc in market_docs:
        data = doc.to_dict()
        ticker = doc.id.upper()
        market_data[ticker] = {
            "sma50": data.get("sma50"),
            "sma200": data.get("sma200")
        }
    
    # 2. Iterar pela coleção 'ativos' e atualizar
    ativos_ref = db.collection("ativos")
    ativos_docs = ativos_ref.stream()
    
    updated_count = 0
    not_found_count = 0
    
    for doc in ativos_docs:
        data = doc.to_dict()
        ticker = data.get("ticker", "").upper()
        
        if not ticker:
            continue
            
        if ticker in market_data:
            smas = market_data[ticker]
            if smas["sma50"] is not None or smas["sma200"] is not None:
                doc.reference.update({
                    "sma50": smas["sma50"],
                    "sma200": smas["sma200"],
                    "lastSmaUpdate": firestore.SERVER_TIMESTAMP
                })
                updated_count += 1
        else:
            not_found_count += 1
            
    print(f"Sucesso: {updated_count} documentos em 'ativos' atualizados.")
    if not_found_count > 0:
        print(f"Aviso: {not_found_count} tickers não encontrados em 'acoesDividendos'.")

if __name__ == "__main__":
    sync_smas_to_ativos()
