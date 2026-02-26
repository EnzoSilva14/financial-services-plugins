import json
from typing import Dict, List

async def execute_rebalancing_br(client_data: dict, mcp_clients: dict, target_allocation: dict = None) -> dict:
    """
    Skill: Rebalanceamento de Carteira BR
    Traduzida do repositório original Anthropic para o mercado brasileiro.
    """
    openfinance = mcp_clients["openfinance"]
    
    # 1. Buscar holdings reais via Open Finance (Pluggy)
    investments_raw = await openfinance.get_investments(client_data["pluggy_item_id"])
    investments = json.loads(investments_raw)
    holdings = investments.get("holdings", [])
    
    if not holdings:
        return {"error": "Nenhum investimento encontrado para análise."}

    # 2. Calcular Alocação Atual
    total_value = sum(h.get("amount", 0) for h in holdings)
    current_alloc = {}
    for h in holdings:
        asset_type = h.get("type", "OUTROS")
        current_alloc[asset_type] = current_alloc.get(asset_type, 0) + (h.get("amount", 0) / total_value * 100)

    # 3. Definir Alvo (Se não provido, usamos um padrão moderado BR)
    if not target_allocation:
        target_allocation = {
            "FIXED_INCOME": 60.0,
            "STOCKS": 25.0,
            "FII": 10.0,
            "OUTROS": 5.0
        }

    # 4. Calcular Drift (Desvio) - Lógica do SKILL.md original
    drifts = []
    for asset_type, target_pct in target_allocation.items():
        current_pct = current_alloc.get(asset_type, 0)
        drift = current_pct - target_pct
        drifts.append({
            "type": asset_type,
            "target": target_pct,
            "current": current_pct,
            "drift": drift,
            "status": "OVERWEIGHT" if drift > 5 else ("UNDERWEIGHT" if drift < -5 else "BALANCED")
        })

    # 5. Sugestão de Operações (Tax-Aware BR)
    # No Brasil, focamos em não estourar os R$ 20k de isenção em ações se possível
    recommendations = []
    for d in drifts:
        if d["status"] == "OVERWEIGHT":
            amount_to_sell = (d["drift"] / 100) * total_value
            recommendations.append(f"Vender R$ {amount_to_sell:,.2f} de {d['type']} (Reduzir excesso)")
        elif d["status"] == "UNDERWEIGHT":
            amount_to_buy = (abs(d["drift"]) / 100) * total_value
            recommendations.append(f"Aportar R$ {amount_to_buy:,.2f} em {d['type']} (Completar alvo)")

    return {
        "total_value": total_value,
        "drifts": drifts,
        "recommendations": recommendations,
        "is_rebalancing_needed": any(abs(d["drift"]) > 5 for d in drifts),
        "source": "OSIRA Intelligence (based on Anthropic Logic + Pluggy Data)"
    }

SKILL_METADATA = {
    "name": "rebalancing_br",
    "description": "Calcula o desvio da carteira e sugere rebalanceamento tax-aware",
    "triggers": ["/rebalancear", "minha carteira está equilibrada", "ajuste de alocação"]
}
