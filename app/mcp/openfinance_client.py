import httpx
import json
from app.config import get_settings

settings = get_settings()

class OpenFinanceMCP:
    """Cliente para o MCP Server de Open Finance"""
    
    def __init__(self):
        self.base_url = settings.MCP_OPENFINANCE_URL
    
    async def get_investments(self, item_id: str) -> str:
        """Busca investimentos via Open Finance"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_investments",
                        "arguments": {"item_id": item_id}
                    },
                    "id": "1"
                }
            )
            data = response.json()
            return data.get("result", {}).get("content", [{}])[0].get("text", "{}")
    
    async def get_accounts(self, item_id: str) -> str:
        """Busca contas bancárias"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_accounts",
                        "arguments": {"item_id": item_id}
                    },
                    "id": "1"
                }
            )
            data = response.json()
            return data.get("result", {}).get("content", [{}])[0].get("text", "{}")
    
    async def get_transactions(self, item_id: str, start_date: str, end_date: str) -> str:
        """Busca transações"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_transactions",
                        "arguments": {
                            "item_id": item_id,
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    },
                    "id": "1"
                }
            )
            data = response.json()
            return data.get("result", {}).get("content", [{}])[0].get("text", "{}")
