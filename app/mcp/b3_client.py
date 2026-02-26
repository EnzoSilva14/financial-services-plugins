import httpx
import json
from app.config import get_settings

settings = get_settings()

class B3MCP:
    """Cliente para o MCP Server de B3 Data"""
    
    def __init__(self):
        self.base_url = settings.MCP_B3_URL
    
    async def get_dividends(self, ticker: str) -> str:
        """Busca próximos dividendos"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_dividends",
                        "arguments": {"ticker": ticker}
                    },
                    "id": "1"
                }
            )
            data = response.json()
            return data.get("result", {}).get("content", [{}])[0].get("text", "{}")
    
    async def get_corporate_events(self, ticker: str) -> str:
        """Busca eventos corporativos"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_corporate_events",
                        "arguments": {"ticker": ticker}
                    },
                    "id": "1"
                }
            )
            data = response.json()
            return data.get("result", {}).get("content", [{}])[0].get("text", "{}")
