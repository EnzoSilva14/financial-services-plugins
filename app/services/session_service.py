import redis.asyncio as redis
import json
from typing import List, Dict, Optional
from app.config import get_settings

settings = get_settings()

class SessionService:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Conecta ao Redis"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def get_conversation_history(self, phone_number: str) -> List[Dict]:
        """Busca histórico de conversa"""
        key = f"session:{phone_number}"
        data = await self.redis.get(key)
        
        if data:
            return json.loads(data)
        return []
    
    async def save_conversation_history(
        self, 
        phone_number: str, 
        messages: List[Dict]
    ):
        """Salva histórico de conversa (expira em 1 hora)"""
        key = f"session:{phone_number}"
        await self.redis.setex(
            key,
            settings.SESSION_EXPIRE_SECONDS,
            json.dumps(messages, ensure_ascii=False)
        )
    
    async def clear_session(self, phone_number: str):
        """Limpa sessão do cliente"""
        key = f"session:{phone_number}"
        await self.redis.delete(key)
    
    async def set_user_state(self, phone_number: str, state: str):
        """Define estado do usuário (ex: waiting_for_cpf)"""
        key = f"state:{phone_number}"
        await self.redis.setex(key, 300, state)  # Expira em 5 min
    
    async def get_user_state(self, phone_number: str) -> Optional[str]:
        """Busca estado do usuário"""
        key = f"state:{phone_number}"
        return await self.redis.get(key)
