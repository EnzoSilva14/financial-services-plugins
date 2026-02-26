from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Client
from pydantic import BaseModel

router = APIRouter()

class OnboardingRequest(BaseModel):
    phone_number: str
    name: str
    cpf: str
    email: str

@router.post("/onboarding")
async def onboarding(
    data: OnboardingRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint para onboarding de novos clientes
    """
    # Verificar se já existe
    existing = db.query(Client).filter(
        (Client.phone_number == data.phone_number) | (Client.cpf == data.cpf)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado")
    
    # Criar cliente
    client = Client(
        phone_number=data.phone_number,
        name=data.name,
        cpf=data.cpf,
        email=data.email,
        is_active=True
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return {
        "message": "Cliente cadastrado com sucesso",
        "client_id": client.id
    }

@router.post("/connect-pluggy")
async def connect_pluggy(
    phone_number: str,
    pluggy_item_id: str,
    db: Session = Depends(get_db)
):
    """
    Conecta a conta Pluggy ao cliente
    """
    client = db.query(Client).filter(
        Client.phone_number == phone_number
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    client.pluggy_item_id = pluggy_item_id
    db.commit()
    
    return {"message": "Conta conectada com sucesso"}
