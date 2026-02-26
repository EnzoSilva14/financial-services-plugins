import httpx
import json
from app.config import get_settings

settings = get_settings()

class ComDinheiroMCP:
    """Cliente para o MCP Server de ComDinheiro"""
    
    def __init__(self):
        self.base_url = settings.MCP_COMDINHEIRO_URL
    
    async def get_current_prices(self, tickers: list) -> str:
        """Busca cotações atuais"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_current_prices",
                        "arguments": {"tickers": tickers}
                    },
                    "id": "1"
                }
            )
            data = response.json()
            return data.get("result", {}).get("content", [{}])[0].get("text", "{}")
    
    async def get_price_history(self, ticker: str, start_date: str, end_date: str) -> str:
        """Busca histórico de preços"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_price_history",
                        "arguments": {
                            "ticker": ticker,
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    },
                    "id": "1"
                }
            )
            data = response.json()
            return data.get("result", {}).get("content", [{}])[0].get("text", "{}")
    
    async def get_fund_data(self, cnpj: str) -> str:
        """Busca dados de fundos"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_fund_data",
                        "arguments": {"cnpj": cnpj}
                    },
                    "id": "1"
                }
            )
            data = response.json()
            return data.get("result", {}).get("content", [{}])[0].get("text", "{}")
