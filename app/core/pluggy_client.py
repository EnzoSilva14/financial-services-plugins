import os
import requests
import json

class RealOpenFinanceClient:
    """Implementação real de conexão com o Pluggy via Open Finance"""
    def __init__(self, client_id=None, client_secret=None):
        self.api_url = "https://api.pluggy.ai"
        self.client_id = client_id or os.getenv("PLUGGY_CLIENT_ID") or os.getenv("clientId")
        self.client_secret = client_secret or os.getenv("PLUGGY_CLIENT_SECRET") or os.getenv("clientSecret")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Credenciais Pluggy não encontradas no .env")
            
        self.api_key = self._get_api_key()

    def _get_api_key(self):
        """Autentica no Pluggy e gera API Key"""
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
        response = requests.post(f"{self.api_url}/auth", json=payload)
        if response.status_code == 200:
            return response.json().get("apiKey")
        else:
            raise Exception(f"Erro na autenticação Pluggy: {response.text}")

    async def get_accounts(self, item_id):
        headers = {"X-API-KEY": self.api_key}
        response = requests.get(f"{self.api_url}/accounts?itemId={item_id}", headers=headers)
        if response.status_code == 200:
            return json.dumps(response.json(), ensure_ascii=False)
        return json.dumps({"results": []})

    async def get_investments(self, item_id):
        headers = {"X-API-KEY": self.api_key}
        response = requests.get(f"{self.api_url}/investments?itemId={item_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            holdings = []
            for inv in data.get("results", []):
                balance = inv.get("balance") or inv.get("value") or 0
                inst_data = inv.get("institution") or {}
                holdings.append({
                    "name": inv.get("name", "Sem Nome"),
                    "ticker": inv.get("symbol") or inv.get("name"),
                    "amount": float(balance),
                    "quantity": inv.get("quantity", 0),
                    "type": inv.get("type", "OUTROS"),
                    "institution": inst_data.get("name", "Desconhecida"),
                    "cost_basis": inv.get("currencyCode")
                })
            return json.dumps({"holdings": holdings}, ensure_ascii=False)
        return json.dumps({"holdings": []})

    async def get_transactions(self, item_id, page_size=100):
        headers = {"X-API-KEY": self.api_key}
        response = requests.get(f"{self.api_url}/transactions?itemId={item_id}&pageSize={page_size}", headers=headers)
        if response.status_code == 200:
            return json.dumps(response.json(), ensure_ascii=False)
        return json.dumps({"results": []})
