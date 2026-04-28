import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from scraper.transformer import clean_row_for_firestore

class FirebaseManager:
    """
    Gere a persistência de dados no Firebase Firestore.
    """
    def __init__(self):
        self.db = None
        self._initialize()

    def _initialize(self):
        """
        Inicializa o Firebase usando o caminho do ficheiro JSON no .env.
        """
        try:
            # Já foi inicializado?
            if firebase_admin._apps and self.db:
                return

            cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            print(f"DEBUG Firebase: Tentativa de inicializar com path: {cred_path}")
            
            if not cred_path:
                print("DEBUG Firebase: Caminho (FIREBASE_SERVICE_ACCOUNT_JSON) está VAZIO.")
                return

            if "COLE_O_CAMINHO" in cred_path:
                print(f"DEBUG Firebase: O caminho ainda contém o placeholder: {cred_path}")
                return

            if not os.path.exists(cred_path):
                print(f"DEBUG Firebase: O ficheiro NÃO EXISTE no caminho: {cred_path}")
                return

            # Se chegámos aqui, o path parece válido
            print(f"DEBUG Firebase: Ficheiro encontrado! A configurar credenciais...")
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("Firebase: Ligação ao Firestore estabelecida com SUCESSO.")
        except Exception as e:
            print(f"❌ Firebase: Erro fatal na inicialização: {e}")
            import traceback
            traceback.print_exc()
            self.db = None

    def save_batch(self, payload):
        """
        Guarda o resultado de um batch no Firestore (Colecao 'scrapes').
        """
        if not self.db:
            print("Firebase: Base de dados nao inicializada corretamente.")
            return False

        try:
            # Coleção: scrapes
            # Um documento por batch
            batch_id = f"batch_{payload.get('source')}_{payload.get('market')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Adiciona timestamp do Firestore para ordenação
            payload['created_at'] = firestore.SERVER_TIMESTAMP
            
            self.db.collection("scrapes").document(batch_id).set(payload)
            print(f"Firebase: Batch guardado com ID: {batch_id}")
            return True
        except Exception as e:
            print(f"Firebase: Erro ao guardar batch: {e}")
            return False

    def save_batch_to_market_data(self, payload):
        """
        Percorre as linhas do batch e atualiza cada ticker na colecao 'acoesDividendos'.
        """
        if not self.db:
            print("Firebase: Base de dados nao inicializada.")
            return False

        rows = payload.get("rows", [])
        if not rows:
            print("Firebase: Nenhum dado (rows) para sincronizar.")
            return False

        success_count = 0
        for row in rows:
            ticker = row.get("ticker")
            if not ticker or ticker == "-":
                continue
            
            # Limpa chaves e valores para o Firestore usando o transformer
            clean_row = clean_row_for_firestore(row)
            
            if self.update_market_data(ticker, clean_row):
                success_count += 1
        
        print(f"Firebase: Sincronizados {success_count}/{len(rows)} tickers com a colecao 'acoesDividendos'.")
        return success_count > 0

    def get_all_tickers(self):
        """
        Lê todos os tickers da coleção 'tickers'.
        """
        if not self.db:
            print("Firebase: Base de dados nao inicializada.")
            return []

        try:
            docs = self.db.collection("acoesDividendos").stream()
            tickers = []
            for d in docs:
                data = d.to_dict()
                if "ticker" in data:
                    tickers.append(data["ticker"].upper())
            return tickers
        except Exception as e:
            print(f"Firebase: Erro ao ler tickers: {e}")
            return []

    def update_market_data(self, ticker, data):
        """
        Atualiza ou cria um documento na coleção 'marketData'.
        Campos com valor None são REMOVIDOS do payload para não
        sobrescrever dados existentes válidos no Firestore.
        """
        if not self.db:
            return False

        try:
            # Remove None values — never overwrite good data with null
            data = {k: v for k, v in data.items() if v is not None}

            # Adiciona timestamp do servidor
            data['updatedAt'] = firestore.SERVER_TIMESTAMP
            data['ultimaAtu'] = firestore.SERVER_TIMESTAMP
            data['ticker'] = ticker
            
            self.db.collection("acoesDividendos").document(ticker).set(data, merge=True)
            print(f"Firebase: acoesDividendos atualizado para {ticker}")
            
            # Propagar para a coleção 'ativos' (portfólio)
            self._propagate_to_portfolio(ticker, data)
            
            return True
        except Exception as e:
            print(f"Firebase: Erro ao atualizar marketData para {ticker}: {e}")
            return False

    def _propagate_to_portfolio(self, ticker, data):
        """
        Atualiza campos relevantes (preço, SMAs) em todos os documentos 
        da coleção 'ativos' que correspondam ao ticker.
        """
        if not self.db:
            return

        try:
            # Selecionar apenas campos que fazem sentido no portfólio
            fields_to_sync = [
                "valorStock", "sma50", "sma200", "priceChange_1d", 
                "rsi", "yield", "pe", "roe", "roa"
            ]
            sync_payload = {k: data[k] for k in fields_to_sync if k in data}
            
            if not sync_payload:
                return

            # Procurar documentos com este ticker na coleção 'ativos'
            ativos_ref = self.db.collection("ativos")
            query = ativos_ref.where("ticker", "==", ticker).stream()
            
            for doc in query:
                doc.reference.update(sync_payload)
                # print(f"Firebase: Portfólio (ativos) atualizado para {ticker} (doc {doc.id})")
                
        except Exception as e:
            print(f"Firebase: Erro ao propagar para portfólio para {ticker}: {e}")

# Instância única para reutilização
firebase_manager = FirebaseManager()
