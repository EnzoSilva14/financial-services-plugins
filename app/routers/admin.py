from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Client, ConversationLog
from typing import List

router = APIRouter()

@router.get("/clients")
async def list_clients(db: Session = Depends(get_db)):
    """
    Lista todos os clientes
    """
    clients = db.query(Client).all()
    return {"clients": clients}

@router.get("/clients/{client_id}")
async def get_client(client_id: int, db: Session = Depends(get_db)):
    """
    Busca um cliente específico
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return client

@router.get("/clients/{client_id}/conversations")
async def get_client_conversations(
    client_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Busca histórico de conversas de um cliente
    """
    conversations = db.query(ConversationLog).filter(
        ConversationLog.client_id == client_id
    ).order_by(ConversationLog.created_at.desc()).limit(limit).all()
    
    return {"conversations": conversations}

@router.patch("/clients/{client_id}/active")
async def toggle_client_active(
    client_id: int,
    is_active: bool,
    db: Session = Depends(get_db)
):
    """
    Ativa ou desativa um cliente
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    client.is_active = is_active
    db.commit()
    
    return {"message": f"Cliente {'ativado' if is_active else 'desativado'} com sucesso"}
