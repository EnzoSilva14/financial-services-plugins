import json

async def execute_tax_harvesting_br(client_data: dict, mcp_clients: dict) -> dict:
    """
    Skill: Tax-Loss Harvesting (Colheita de Prejuízo)
    Identifica oportunidades de vender ativos em prejuízo para abater IR futuro.
    """
    openfinance = mcp_clients["openfinance"]
    
    # 1. Buscar posições reais
    investments_raw = await openfinance.get_investments(client_data["pluggy_item_id"])
    investments = json.loads(investments_raw)
    holdings = investments.get("holdings", [])
    
    candidates = []
    total_potential_loss = 0
    
    # 2. Identificar candidatos (Preço Atual < Preço Médio)
    for h in holdings:
        if h.get("type") == "STOCKS":
            current_value = h.get("amount", 0)
            quantity = h.get("quantity", 0)
            cost_basis = h.get("cost_basis", 0) # Preço médio do Pluggy
            
            if quantity > 0 and cost_basis > 0:
                market_price = current_value / quantity
                if market_price < cost_basis:
                    loss = (cost_basis - market_price) * quantity
                    candidates.append({
                        "ticker": h.get("ticker"),
                        "quantity": quantity,
                        "current_price": market_price,
                        "cost_basis": cost_basis,
                        "potential_loss": loss,
                        "is_under_20k": current_value < 20000
                    })
                    total_potential_loss += loss

    return {
        "candidates": sorted(candidates, key=lambda x: x["potential_loss"], reverse=True),
        "total_potential_loss": total_potential_loss,
        "tax_rule_reminder": "Lembre-se: Vendas de ações até R$ 20k/mês são isentas de IR no Brasil.",
        "recommendation": "Considere vender os ativos acima para gerar prejuízo fiscal e recomprar em seguida (atento ao wash sale de 30 dias se quiser evitar questionamentos)."
    }

SKILL_METADATA = {
    "name": "tax_harvesting_br",
    "description": "Busca oportunidades de redução de imposto via prejuízo fiscal",
    "triggers": ["/ir", "como pagar menos imposto", "prejuízo fiscal", "tax loss"]
}
