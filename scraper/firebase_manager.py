import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

class FirebaseManager:
    """
    Gere a persistência de dados no Firebase Firestore.
    """
    def __init__(self):
        self.db = None
        self._initialize()

    def _initialize(self):
        # Tenta inicializar usando o caminho do ficheiro .json definido no .env
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        
        if not cred_path or not os.path.exists(cred_path):
            print(f"Firebase: Ficheiro de credenciais nao encontrado em: {cred_path}")
            return

        try:
            # Evita re-inicialização se já existir uma app
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("Firebase: Ligacao ao Firestore estabelecida com sucesso.")
        except Exception as e:
            print(f"Firebase: Erro ao inicializar: {e}")

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
        """
        if not self.db:
            return False

        try:
            # Adiciona timestamp do servidor
            data['updatedAt'] = firestore.SERVER_TIMESTAMP
            data['ultimaAtu'] = firestore.SERVER_TIMESTAMP
            data['ticker'] = ticker
            
            self.db.collection("acoesDividendos").document(ticker).set(data, merge=True)
            print(f"Firebase: acoesDividendos atualizado para {ticker}")
            return True
        except Exception as e:
            print(f"Firebase: Erro ao atualizar marketData para {ticker}: {e}")
            return False

# Instância única para reutilização
firebase_manager = FirebaseManager()
