"""
Skill: Cálculo de Imposto de Renda BR

Calcula a posição de IR do cliente considerando regras brasileiras.
"""
import json
from datetime import datetime, timedelta

async def execute_imposto_renda_br(client_data: dict, mcp_clients: dict) -> dict:
    """
    Calcula posição de IR do cliente
    
    Regras brasileiras:
    - Day trade: 20% de imposto
    - Swing trade: 15% de imposto
    - Vendas < R$ 20k/mês em ações: isento
    - FIIs: sempre tributado nas vendas
    """
    openfinance = mcp_clients["openfinance"]
    
    # Buscar transações dos últimos 12 meses
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    transactions_raw = await openfinance.get_transactions(
        client_data["pluggy_item_id"],
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    transactions = json.loads(transactions_raw).get("transactions", [])
    
    # Classificar operações
    day_trades = []
    swing_trades = []
    long_term = []
    
    for tx in transactions:
        if tx.get("type") == "SELL":
            # Lógica simplificada - em produção, fazer matching com compras
            holding_days = tx.get("holding_days", 0)
            
            if holding_days == 0:
                day_trades.append(tx)
            elif holding_days < 30:
                swing_trades.append(tx)
            else:
                long_term.append(tx)
    
    # Calcular impostos
    day_trade_tax = sum(tx.get("profit", 0) * 0.20 for tx in day_trades if tx.get("profit", 0) > 0)
    swing_trade_tax = sum(tx.get("profit", 0) * 0.15 for tx in swing_trades if tx.get("profit", 0) > 0)
    
    # Verificar isenção de R$ 20k/mês
    # TODO: Agrupar por mês e aplicar isenção
    
    total_tax_due = day_trade_tax + swing_trade_tax
    
    return {
        "day_trade_operations": len(day_trades),
        "day_trade_tax": day_trade_tax,
        "swing_trade_operations": len(swing_trades),
        "swing_trade_tax": swing_trade_tax,
        "total_tax_due": total_tax_due,
        "warning": "⚠️ Cálculo simplificado. Consulte um contador para declaração oficial."
    }


SKILL_METADATA = {
    "name": "imposto_renda_br",
    "description": "Calcula posição de imposto de renda brasileiro",
    "triggers": [
        "/ir",
        "imposto de renda",
        "quanto devo de imposto",
        "darf"
    ]
}
