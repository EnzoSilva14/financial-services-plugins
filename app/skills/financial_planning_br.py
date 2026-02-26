import json
from datetime import datetime, timedelta

async def execute_financial_planning_br(client_data: dict, mcp_clients: dict) -> dict:
    """
    Skill: Planejamento Financeiro e Fluxo de Caixa
    Analisa transações passadas para prever capacidade de aporte.
    """
    openfinance = mcp_clients["openfinance"]
    
    # 1. Buscar transações dos últimos 90 dias
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    transactions_raw = await openfinance.get_transactions(client_data["pluggy_item_id"], start_date, end_date)
    transactions = json.loads(transactions_raw)
    
    # 2. Analisar Receitas vs Despesas
    inflow = 0
    outflow = 0
    categories = {}
    
    for tx in transactions.get("results", []):
        amount = tx.get("amount", 0)
        if amount > 0:
            inflow += amount
        else:
            outflow += abs(amount)
            cat = tx.get("category", "OUTROS")
            categories[cat] = categories.get(cat, 0) + abs(amount)

    avg_monthly_inflow = inflow / 3
    avg_monthly_outflow = outflow / 3
    monthly_surplus = avg_monthly_inflow - avg_monthly_outflow

    return {
        "monthly_summary": {
            "avg_receitas": avg_monthly_inflow,
            "avg_despesas": avg_monthly_outflow,
            "capacidade_aporte": monthly_surplus
        },
        "top_despesas": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3],
        "financial_health": "POSITIVE" if monthly_surplus > 0 else "NEGATIVE",
        "recommendation": f"Sua capacidade de aporte mensal média é de R$ {monthly_surplus:,.2f}. Sugerimos automatizar um aporte de pelo menos 50% deste valor."
    }

SKILL_METADATA = {
    "name": "financial_planning",
    "description": "Análise de fluxo de caixa e planejamento de aposentadoria/aportes",
    "triggers": ["/plano", "quanto posso investir", "meu fluxo de caixa", "planejamento"]
}
