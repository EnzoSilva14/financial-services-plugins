import anthropic
from typing import List, Dict, Any
import json
from app.config import get_settings

settings = get_settings()

class ClaudeService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
    def get_system_prompt(self, client_data: dict) -> str:
        """Gera system prompt customizado para o cliente"""
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

Nota: Use prioritariamente os valores de 'balance' e 'value' retornados pelo Open Finance, pois refletem a posição real nas instituições.

ESTILO DE COMUNICAÇÃO:
- Conciso (WhatsApp = mensagens curtas, max 300 chars)
- Use emojis apropriados: 📊💰📈📉🎯
- Sempre cite as fontes ("Fonte: Open Finance via {client_data['institutions'][0] if client_data['institutions'] else 'sua corretora'}")

ESTRATÉGIA DE ANÁLISE:
1. Busque os investimentos via Open Finance.
2. Agrupe por classe de ativos (Ações, Renda Fixa, Fundos).
3. Calcule a alocação percentual baseada nos valores totais retornados.
4. Para dúvidas sobre rentabilidade histórica, use o histórico de transações.

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
        Envia mensagens para o Claude com suporte a MCP tools
        """
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=4096,
            system=self.get_system_prompt(client_data),
            messages=messages,
            tools=tools
        )
        
        return {
            "content": response.content,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }
    
    def extract_text_response(self, content: List[Any]) -> str:
        """Extrai texto da resposta do Claude"""
        texts = []
        for block in content:
            if hasattr(block, 'type') and block.type == "text":
                texts.append(block.text)
        return "\n".join(texts)
    
    def extract_tool_calls(self, content: List[Any]) -> List[Dict[str, Any]]:
        """Extrai tool calls da resposta do Claude"""
        tool_calls = []
        for block in content:
            if hasattr(block, 'type') and block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        return tool_calls
