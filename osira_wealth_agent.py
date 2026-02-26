import os
import json
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Configura caminhos
ROOT_PATH = Path(__file__).parent
sys.path.append(str(ROOT_PATH))

# Carrega ambiente
load_dotenv(".env")

# Importa Core e Skills
from app.core.pluggy_client import RealOpenFinanceClient
from app.skills.client_review_br import execute_client_review_br
from app.skills.financial_planning_br import execute_financial_planning_br
from app.skills.rebalancing_br import execute_rebalancing_br
from app.skills.tax_harvesting_br import execute_tax_harvesting_br
from app.skills.previdencia_br import execute_previdencia_br

# Cores para o terminal
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class OsiraWealthPOC:
    def __init__(self):
        self.item_id = os.getenv("itemId")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        if not self.api_key:
            print(f"{bcolors.FAIL}❌ ERRO: OPENAI_API_KEY não configurada no .env{bcolors.ENDC}")
            sys.exit(1)

        print(f"🏛️  Inicializando Conexão Open Finance...")
        self.pluggy = RealOpenFinanceClient()
        self.openai = OpenAI(api_key=self.api_key)
        
        self.mcp_clients = {"openfinance": self.pluggy, "comdinheiro": None}
        self.client_data = {
            "name": "Enzo Barroso", 
            "pluggy_item_id": self.item_id, 
            "cpf": "Real Data",
            "institutions": ["Itaú Personnalité"]
        }

    def get_system_prompt(self):
        return f"""
        Você é o OSIRA Wealth Agent, um assessor de elite do mercado brasileiro (Multi-Family Office).
        Seu tom é profissional, sofisticado e focado em clareza patrimonial total.
        
        DIRETRIZES:
        1. Patrimônio Total = Saldo em Conta + Investimentos.
        2. Seja proativo: Se houver dinheiro parado na conta, sugira rentabilizar.
        3. Se o Cartão de Crédito estiver alto comparado ao patrimônio, alerte o cliente.
        4. Use emojis financeiros (💰, 🏛️, 📈, 🚀) e bullet points.
        5. Termine com: "⚠️ Isso não é recomendação oficial."
        """

    async def call_tool(self, name, args):
        """Mapeia as chamadas da IA para as Skills brasileiras"""
        try:
            if name == "get_client_portfolio":
                return await execute_client_review_br(self.client_data, self.mcp_clients)
            elif name == "analyze_portfolio_drift":
                return await execute_rebalancing_br(self.client_data, self.mcp_clients)
            elif name == "identify_tax_harvesting":
                return await execute_tax_harvesting_br(self.client_data, self.mcp_clients)
            elif name == "project_financial_cashflow":
                return await execute_financial_planning_br(self.client_data, self.mcp_clients)
            elif name == "get_pension_advice":
                return await execute_previdencia_br(self.client_data, self.mcp_clients)
        except Exception as e:
            return {"error": str(e)}
        return {"error": "Tool não encontrada"}

    async def start_chat(self):
        print(f"\n{bcolors.BOLD}{'-'*60}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}🟢 OSIRA WEALTH AGENT POC - ONLINE{bcolors.ENDC}")
        print(f"Conectado: {self.client_data['institutions'][0]}")
        print(f"{bcolors.BOLD}{'-'*60}{bcolors.ENDC}\n")
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        tools = [
            {"type": "function", "function": {"name": "get_client_portfolio", "description": "Ver patrimônio total (Conta + Investimentos)"}},
            {"type": "function", "function": {"name": "analyze_portfolio_drift", "description": "Analisar rebalanceamento 60/40"}},
            {"type": "function", "function": {"name": "identify_tax_harvesting", "description": "Buscar prejuízo fiscal para IR"}},
            {"type": "function", "function": {"name": "project_financial_cashflow", "description": "Analisar fluxo de caixa e aportes"}},
            {"type": "function", "function": {"name": "get_pension_advice", "description": "Consultoria PGBL vs VGBL"}}
        ]

        while True:
            user_input = input(f"{bcolors.BOLD}👤 Você:{bcolors.ENDC} ")
            if user_input.lower() in ["sair", "exit", "quit"]: break
            
            messages.append({"role": "user", "content": user_input})
            
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            msg = response.choices[0].message
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    print(f"⚙️  Executando: {bcolors.OKBLUE}{tool_call.function.name}{bcolors.ENDC}...")
                    result = await self.call_tool(tool_call.function.name, {})
                    
                    messages.append(msg)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": json.dumps(result)
                    })
                
                response = self.openai.chat.completions.create(model=self.model, messages=messages)
                final_text = response.choices[0].message.content
            else:
                final_text = msg.content

            messages.append({"role": "assistant", "content": final_text})
            print(f"\n{bcolors.BOLD}🤖 OSIRA:{bcolors.ENDC} {final_text}\n")

if __name__ == "__main__":
    poc = OsiraWealthPOC()
    asyncio.run(poc.start_chat())
