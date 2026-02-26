from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

Base = declarative_base()

# SQLAlchemy Models
class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String, unique=True, index=True)
    name = Column(String)
    cpf = Column(String, unique=True)
    email = Column(String)
    pluggy_item_id = Column(String)  # ID da conexão Open Finance
    institutions = Column(JSON)  # ["XP", "BTG", "Nubank"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer)
    phone_number = Column(String, index=True)
    role = Column(String)  # "user" ou "assistant"
    message = Column(String)
    mcp_calls = Column(JSON)  # Log de chamadas MCP
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models (para API)
class WhatsAppMessage(BaseModel):
    From: str  # whatsapp:+5511999999999
    Body: str
    MessageSid: str

class MCPToolCall(BaseModel):
    tool_name: str
    arguments: dict
    
class ChatMessage(BaseModel):
    role: str
    content: str
    
class PortfolioSummary(BaseModel):
    total_value: float
    daily_change: float
    daily_change_percent: float
    top_holdings: List[dict]
    allocation: dict
