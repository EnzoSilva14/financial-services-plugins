from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.models import WhatsAppMessage, Client
from app.services.claude_service import ClaudeService
from app.services.whatsapp_service import WhatsAppService
from app.services.session_service import SessionService
from app.mcp.openfinance_client import OpenFinanceMCP
from app.mcp.comdinheiro_client import ComDinheiroMCP
from app.mcp.b3_client import B3MCP
from app.database import get_db
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

claude_service = ClaudeService()
whatsapp_service = WhatsAppService()
session_service = SessionService()

# MCP Clients
openfinance_mcp = OpenFinanceMCP()
comdinheiro_mcp = ComDinheiroMCP()
b3_mcp = B3MCP()

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook que recebe mensagens do WhatsApp
    """
    form_data = await request.form()
    
    phone_number = form_data.get("From", "").replace("whatsapp:", "")
    message_body = form_data.get("Body", "")
    message_sid = form_data.get("MessageSid", "")
    
    logger.info(f"📱 Mensagem de {phone_number}: {message_body}")
    
    # Processa em background para não travar o webhook
    background_tasks.add_task(
        process_message,
        phone_number,
        message_body,
        message_sid,
        db
    )
    
    # Responde imediatamente para Twilio
    return Response(content="", status_code=200)

async def process_message(
    phone_number: str,
    message_body: str,
    message_sid: str,
    db: Session
):
    """
    Processa a mensagem do cliente
    """
    try:
        # 1. Buscar cliente no banco
        client = db.query(Client).filter(
            Client.phone_number == phone_number
        ).first()
        
        if not client:
            # Cliente novo - iniciar onboarding
            await whatsapp_service.send_message(
                phone_number,
                "👋 Olá! Bem-vindo à OSIRA Wealth.\n\n"
                "Para começar, conecte suas contas:\n"
                "🔗 https://app.osira.com.br/connect?phone=" + phone_number
            )
            return
        
        if not client.is_active:
            await whatsapp_service.send_message(
                phone_number,
                "⚠️ Sua conta está inativa. Entre em contato com suporte."
            )
            return
        
        # 2. Carregar histórico da conversa
        conversation_history = await session_service.get_conversation_history(phone_number)
        
        # 3. Adicionar mensagem do usuário
        conversation_history.append({
            "role": "user",
            "content": message_body
        })
        
        # 4. Preparar tools MCP disponíveis
        mcp_tools = get_mcp_tools_definition()
        
        # 5. Chamar Claude
        client_data = {
            "name": client.name,
            "cpf": client.cpf,
            "institutions": client.institutions or []
        }
        
        response = await claude_service.chat(
            messages=conversation_history,
            client_data=client_data,
            tools=mcp_tools
        )
        
        # 6. Processar resposta
        if response["stop_reason"] == "tool_use":
            # Claude quer chamar tools MCP
            tool_calls = claude_service.extract_tool_calls(response["content"])
            
            # Adicionar resposta do Claude ao histórico
            conversation_history.append({
                "role": "assistant",
                "content": response["content"]
            })
            
            # Executar cada tool call
            tool_results = []
            for tool_call in tool_calls:
                result = await execute_mcp_tool(
                    tool_call["name"],
                    tool_call["input"],
                    client
                )
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call["id"],
                    "content": result
                })
            
            # Adicionar tool results ao histórico
            conversation_history.append({
                "role": "user",
                "content": tool_results
            })
            
            # Chamar Claude novamente com os resultados
            final_response = await claude_service.chat(
                messages=conversation_history,
                client_data=client_data,
                tools=mcp_tools
            )
            
            assistant_message = claude_service.extract_text_response(
                final_response["content"]
            )
            
        else:
            # Resposta direta sem tool calls
            assistant_message = claude_service.extract_text_response(
                response["content"]
            )
        
        # 7. Adicionar resposta final ao histórico
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # 8. Salvar sessão
        await session_service.save_conversation_history(
            phone_number,
            conversation_history
        )
        
        # 9. Enviar mensagem pelo WhatsApp
        await whatsapp_service.send_message(phone_number, assistant_message)
        
        logger.info(f"✅ Resposta enviada para {phone_number}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}")
        await whatsapp_service.send_message(
            phone_number,
            "😔 Desculpe, tive um problema ao processar sua mensagem. Tente novamente."
        )

def get_mcp_tools_definition():
    """Define as tools MCP disponíveis"""
    return [
        {
            "name": "open_finance_get_investments",
            "description": "Busca investimentos do cliente via Open Finance",
            "input_schema": {
                "type": "object",
                "properties": {
                    "cpf": {
                        "type": "string",
                        "description": "CPF do cliente"
                    }
                },
                "required": ["cpf"]
            }
        },
        {
            "name": "comdinheiro_get_prices",
            "description": "Cotações atuais da B3",
            "input_schema": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de tickers (ex: ['ITUB4', 'PETR4'])"
                    }
                },
                "required": ["tickers"]
            }
        },
        {
            "name": "b3_get_dividends",
            "description": "Próximos dividendos de uma ação",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Ticker da ação (ex: 'ITUB4')"
                    }
                },
                "required": ["ticker"]
            }
        }
    ]

async def execute_mcp_tool(tool_name: str, arguments: dict, client: Client) -> str:
    """
    Executa uma tool MCP e retorna o resultado
    """
    try:
        if tool_name == "open_finance_get_investments":
            return await openfinance_mcp.get_investments(client.pluggy_item_id)
        
        elif tool_name == "comdinheiro_get_prices":
            return await comdinheiro_mcp.get_current_prices(arguments["tickers"])
        
        elif tool_name == "b3_get_dividends":
            return await b3_mcp.get_dividends(arguments["ticker"])
        
        else:
            return json.dumps({"error": "Tool desconhecida"})
    
    except Exception as e:
        logger.error(f"Erro ao executar tool {tool_name}: {e}")
        return json.dumps({"error": str(e)})
