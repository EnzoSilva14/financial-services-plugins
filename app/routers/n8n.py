from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Client
from app.services.claude_service import ClaudeService
from app.services.session_service import SessionService
from app.mcp.openfinance_client import OpenFinanceMCP
from app.mcp.comdinheiro_client import ComDinheiroMCP
from app.mcp.b3_client import B3MCP
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

claude_service = ClaudeService()
session_service = SessionService()

# MCP Clients
openfinance_mcp = OpenFinanceMCP()
comdinheiro_mcp = ComDinheiroMCP()
b3_mcp = B3MCP()


class N8NMessageRequest(BaseModel):
    """Request do n8n para processar mensagem"""
    phone_number: str
    message: str
    client_data: Optional[Dict] = None
    session_id: Optional[str] = None


class N8NMessageResponse(BaseModel):
    """Response para o n8n"""
    response: str
    mcp_calls_made: List[Dict]
    session_id: str
    needs_human_review: bool = False
    metadata: Optional[Dict] = None


class N8NPortfolioRequest(BaseModel):
    """Request para análise de carteira"""
    cpf: str
    include_prices: bool = True
    include_allocation: bool = True


class N8NWebhookTrigger(BaseModel):
    """Webhook trigger para n8n"""
    event_type: str  # "new_client", "high_risk_trade", "portfolio_alert"
    data: Dict
    timestamp: str


# Endpoint principal para n8n enviar mensagens
@router.post("/n8n/message", response_model=N8NMessageResponse)
async def n8n_process_message(
    request: N8NMessageRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Endpoint para n8n enviar mensagens do cliente e receber resposta do agente
    
    Headers:
        Authorization: Bearer <seu-token-secreto>
    
    Body:
        phone_number: Telefone do cliente
        message: Mensagem do cliente
        client_data: (Opcional) Dados do cliente se já conhecidos
        session_id: (Opcional) ID da sessão para manter contexto
    """
    # TODO: Validar token de autorização
    # if not authorization or authorization != f"Bearer {settings.N8N_SECRET_TOKEN}":
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # 1. Buscar ou criar cliente
        client = db.query(Client).filter(
            Client.phone_number == request.phone_number
        ).first()
        
        if not client and request.client_data:
            # Criar cliente novo se dados foram fornecidos
            client = Client(
                phone_number=request.phone_number,
                name=request.client_data.get("name"),
                cpf=request.client_data.get("cpf"),
                email=request.client_data.get("email"),
                pluggy_item_id=request.client_data.get("pluggy_item_id"),
                is_active=True
            )
            db.add(client)
            db.commit()
            db.refresh(client)
        
        if not client:
            return N8NMessageResponse(
                response="❌ Cliente não encontrado. Por favor, cadastre primeiro.",
                mcp_calls_made=[],
                session_id="",
                needs_human_review=True
            )
        
        # 2. Carregar histórico da conversa
        session_id = request.session_id or f"{request.phone_number}_{int(time.time())}"
        conversation_history = await session_service.get_conversation_history(session_id)
        
        # 3. Adicionar mensagem do usuário
        conversation_history.append({
            "role": "user",
            "content": request.message
        })
        
        # 4. Preparar tools MCP
        mcp_tools = get_mcp_tools_definition()
        
        # 5. Chamar Claude
        client_data = {
            "name": client.name,
            "cpf": client.cpf,
            "institutions": client.institutions or []
        }
        
        mcp_calls_made = []
        
        response = await claude_service.chat(
            messages=conversation_history,
            client_data=client_data,
            tools=mcp_tools
        )
        
        # 6. Processar tool calls se houver
        if response["stop_reason"] == "tool_use":
            tool_calls = claude_service.extract_tool_calls(response["content"])
            
            conversation_history.append({
                "role": "assistant",
                "content": response["content"]
            })
            
            tool_results = []
            for tool_call in tool_calls:
                result = await execute_mcp_tool(
                    tool_call["name"],
                    tool_call["input"],
                    client
                )
                
                mcp_calls_made.append({
                    "tool": tool_call["name"],
                    "arguments": tool_call["input"]
                })
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call["id"],
                    "content": result
                })
            
            conversation_history.append({
                "role": "user",
                "content": tool_results
            })
            
            final_response = await claude_service.chat(
                messages=conversation_history,
                client_data=client_data,
                tools=mcp_tools
            )
            
            assistant_message = claude_service.extract_text_response(
                final_response["content"]
            )
        else:
            assistant_message = claude_service.extract_text_response(
                response["content"]
            )
        
        # 7. Adicionar resposta ao histórico
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # 8. Salvar sessão
        await session_service.save_conversation_history(
            session_id,
            conversation_history
        )
        
        # 9. Verificar se precisa revisão humana
        needs_review = check_needs_human_review(assistant_message, mcp_calls_made)
        
        return N8NMessageResponse(
            response=assistant_message,
            mcp_calls_made=mcp_calls_made,
            session_id=session_id,
            needs_human_review=needs_review,
            metadata={
                "client_id": client.id,
                "client_name": client.name,
                "tokens_used": response["usage"]["input_tokens"] + response["usage"]["output_tokens"]
            }
        )
        
    except Exception as e:
        logger.error(f"Erro no endpoint n8n: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/n8n/portfolio")
async def n8n_get_portfolio(
    request: N8NPortfolioRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint para n8n buscar dados de carteira diretamente
    Útil para criar dashboards ou relatórios automatizados
    """
    try:
        client = db.query(Client).filter(Client.cpf == request.cpf).first()
        
        if not client or not client.pluggy_item_id:
            raise HTTPException(status_code=404, detail="Cliente ou conta não encontrada")
        
        # Buscar investimentos
        investments_raw = await openfinance_mcp.get_investments(client.pluggy_item_id)
        investments = json.loads(investments_raw)
        
        portfolio_data = {
            "client_name": client.name,
            "cpf": request.cpf,
            "total_value": sum(h["amount"] for h in investments.get("holdings", [])),
            "holdings": investments.get("holdings", [])
        }
        
        # Buscar preços se solicitado
        if request.include_prices:
            tickers = [h["ticker"] for h in investments.get("holdings", []) if h.get("ticker")]
            if tickers:
                prices_raw = await comdinheiro_mcp.get_current_prices(tickers)
                portfolio_data["prices"] = json.loads(prices_raw)
        
        # Calcular alocação se solicitado
        if request.include_allocation:
            allocation = {}
            for holding in investments.get("holdings", []):
                asset_type = holding.get("type", "OUTROS")
                allocation[asset_type] = allocation.get(asset_type, 0) + holding["amount"]
            
            portfolio_data["allocation"] = {
                k: {"value": v, "percentage": (v / portfolio_data["total_value"] * 100)}
                for k, v in allocation.items()
            }
        
        return portfolio_data
        
    except Exception as e:
        logger.error(f"Erro ao buscar portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/n8n/webhook/register")
async def n8n_register_webhook(
    webhook_url: str,
    event_types: List[str],
    db: Session = Depends(get_db)
):
    """
    Registra um webhook do n8n para receber eventos
    
    event_types pode incluir:
    - "new_client": Quando novo cliente se cadastra
    - "high_risk_trade": Quando detecta trade de alto risco
    - "portfolio_alert": Quando carteira desvia muito do target
    - "dividend_payment": Quando cliente recebe dividendo
    """
    # TODO: Salvar webhook no banco de dados
    # Por simplicidade, retornando sucesso
    return {
        "message": "Webhook registrado com sucesso",
        "webhook_url": webhook_url,
        "event_types": event_types
    }


@router.get("/n8n/clients")
async def n8n_list_clients(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Lista clientes para o n8n
    Útil para criar workflows que processam clientes em batch
    """
    clients = db.query(Client).filter(
        Client.is_active == True
    ).offset(skip).limit(limit).all()
    
    return {
        "clients": [
            {
                "id": c.id,
                "phone_number": c.phone_number,
                "name": c.name,
                "cpf": c.cpf,
                "has_pluggy_connected": c.pluggy_item_id is not None
            }
            for c in clients
        ]
    }


def check_needs_human_review(message: str, mcp_calls: List) -> bool:
    """
    Verifica se a resposta precisa de revisão humana
    """
    # Flags que indicam necessidade de revisão
    high_risk_keywords = [
        "vender tudo",
        "aportar 100%",
        "risco alto",
        "margin call",
        "perda superior"
    ]
    
    # Verificar palavras-chave
    for keyword in high_risk_keywords:
        if keyword.lower() in message.lower():
            return True
    
    # Se fez muitas chamadas MCP (>5), pode precisar revisão
    if len(mcp_calls) > 5:
        return True
    
    return False


def get_mcp_tools_definition():
    """Define as tools MCP disponíveis"""
    return [
        {
            "name": "open_finance_get_investments",
            "description": "Busca investimentos do cliente via Open Finance",
            "input_schema": {
                "type": "object",
                "properties": {
                    "cpf": {"type": "string", "description": "CPF do cliente"}
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
                        "description": "Lista de tickers"
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
                    "ticker": {"type": "string", "description": "Ticker da ação"}
                },
                "required": ["ticker"]
            }
        }
    ]


async def execute_mcp_tool(tool_name: str, arguments: dict, client: Client) -> str:
    """Executa uma tool MCP"""
    import json
    
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


import time
import json
