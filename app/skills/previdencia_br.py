import json

async def execute_previdencia_br(client_data: dict, mcp_clients: dict) -> dict:
    """
    Skill: Consultor de Previdência Privada
    Analisa a melhor estratégia tributária (PGBL vs VGBL).
    """
    openfinance = mcp_clients["openfinance"]
    
    # 1. Buscar renda estimada via transações (último ano)
    # Aqui simulamos uma análise de 'inflows' para estimar a renda tributável
    investments_raw = await openfinance.get_investments(client_data["pluggy_item_id"])
    investments = json.loads(investments_raw)
    
    # 2. Identificar se já possui previdência
    current_prev = [i for i in investments.get("holdings", []) if "PREVIDENCIA" in str(i.get("type")).upper()]
    
    # 3. Lógica de Decisão (Simplificada para o Agente)
    # Se o cliente faz declaração completa e tem renda alta -> PGBL até 12%
    # Caso contrário -> VGBL
    
    return {
        "current_previdencia_total": sum(p.get("amount", 0) for p in current_prev),
        "holdings": current_prev,
        "recommendation_logic": {
            "PGBL": "Indicado se você faz declaração completa do IR. Permite deduzir até 12% da renda bruta tributável.",
            "VGBL": "Indicado se você faz declaração simplificada ou já atingiu o limite de 12% no PGBL.",
            "Regime_Regressivo": "Melhor para longo prazo (> 10 anos), a alíquota cai para 10%.",
            "Regime_Progressivo": "Melhor se você pretende resgatar valores pequenos e tem pouca renda na aposentadoria."
        },
        "next_steps": "Para uma análise exata, informe sua Renda Bruta Anual Tributável.",
        "disclaimer": "⚠️ Previdência envolve custos de carregamento e gestão. Analise as taxas antes de migrar."
    }

SKILL_METADATA = {
    "name": "previdencia_br",
    "description": "Consultoria sobre PGBL, VGBL e regimes de tributação",
    "triggers": ["/previdencia", "pgbl ou vgbl", "aposentadoria", "previdencia privada"]
}
