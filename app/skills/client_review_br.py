"""
Skill: Resumo de Carteira BR

Gera um resumo completo da carteira do cliente com dados do mercado brasileiro.
"""

import json

async def execute_client_review_br(client_data: dict, mcp_clients: dict) -> dict:
    """
    Executa a skill de revisão de carteira brasileira focada em Open Finance
    """
    openfinance = mcp_clients["openfinance"]
    comdinheiro = mcp_clients.get("comdinheiro") # Pode ser None
    
    # 1. Buscar investimentos e contas via Open Finance
    investments_raw = await openfinance.get_investments(client_data["pluggy_item_id"])
    accounts_raw = await openfinance.get_accounts(client_data["pluggy_item_id"])
    
    investments = json.loads(investments_raw)
    accounts = json.loads(accounts_raw)
    
    # 2. Calcular métricas
    holdings = investments.get("holdings", [])
    inv_value = sum(inv.get("amount", 0) for inv in holdings)
    
    # Soma saldos de conta corrente e poupança (ignora cartão de crédito no patrimônio líquido)
    account_results = accounts.get("results", [])
    cash_value = sum(acc.get("balance", 0) for acc in account_results if acc.get("type") == "BANK")
    credit_used = sum(acc.get("balance", 0) for acc in account_results if acc.get("type") == "CREDIT")
    
    total_value = inv_value + cash_value
    
    # 4. Top holdings
    top_holdings = sorted(
        holdings,
        key=lambda x: x.get("amount", 0),
        reverse=True
    )[:5]
    
    # 5. Alocação por tipo
    allocation = {}
    for holding in holdings:
        asset_type = holding.get("type", "OUTROS")
        allocation[asset_type] = allocation.get(asset_type, 0) + holding.get("amount", 0)
    
    return {
        "total_net_worth": total_value,
        "invested_amount": inv_value,
        "cash_on_hand": cash_value,
        "credit_card_usage": credit_used,
        "top_holdings": sorted(holdings, key=lambda x: x.get("amount", 0), reverse=True)[:5],
        "allocation": allocation,
        "num_positions": len(holdings),
        "institutions": list(set((h.get("institution") or h.get("name")) for h in (holdings + account_results) if (h.get("institution") or h.get("name")))),
        "source": "Open Finance (Pluggy)"
    }


SKILL_METADATA = {
    "name": "client_review_br",
    "description": "Revisão completa de carteira para o mercado brasileiro",
    "triggers": [
        "/carteira",
        "como está minha carteira",
        "meus investimentos",
        "portfolio"
    ]
}
