from openai import OpenAI
from typing import List, Dict, Any
import json
from app.config import get_settings

settings = get_settings()

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def get_system_prompt(self, client_data: dict) -> str:
        """Gera system prompt customizado para o cliente (OpenAI version)"""
        return f"""
Você é o assistente de wealth management da OSIRA, especializado no mercado brasileiro.

DADOS DO CLIENTE:
- Nome: {client_data['name']}
- CPF: {client_data['cpf']}
- Corretoras: {', '.join(client_data['institutions'])}

FERRAMENTAS DISPONÍVEIS:
Você tem acesso aos seguintes dados:

1. open_finance (via Pluggy): Dados REAIS e ATUAIS das contas
   - get_investments(item_id): Retorna holdings, quantidades, preços médios e valores totais atuais.
   - get_accounts(item_id): Saldos em conta corrente e poupança.
   - get_transactions(item_id, start_date, end_date): Histórico de movimentações.

Nota: Use prioritariamente os valores de 'balance' e 'value' retornados pelo Open Finance.

ESTILO DE COMUNICAÇÃO:
- Conciso (WhatsApp = mensagens curtas, max 300 chars)
- Use emojis apropriados: 📊💰📈📉🎯
- Sempre cite as fontes ("Fonte: Open Finance via {client_data['institutions'][0] if client_data['institutions'] else 'sua corretora'}")

DISCLAIMERS OBRIGATÓRIOS:
Sempre que der sugestões de investimento, adicione:
"⚠️ Isso não é recomendação de investimento. Consulte seu assessor."
"""

    async def chat(
        self, 
        messages: List[Dict[str, Any]], 
        client_data: dict,
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Envia mensagens para a OpenAI com suporte a function calling (substituto do MCP no lado do LLM)
        """
        # Converte o formato de tools do Claude para OpenAI
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })

        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": self.get_system_prompt(client_data)},
                *messages
            ],
            tools=openai_tools if openai_tools else None,
            tool_choice="auto" if openai_tools else None
        )
        
        message = response.choices[0].message
        
        return {
            "content": message.content,
            "tool_calls": message.tool_calls,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
        }
