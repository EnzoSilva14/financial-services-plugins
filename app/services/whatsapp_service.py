from twilio.rest import Client
from app.config import get_settings
import httpx
from typing import Optional

settings = get_settings()

class WhatsAppService:
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
    
    async def send_message(self, to: str, body: str) -> str:
        """Envia mensagem de texto"""
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"
        
        message = self.client.messages.create(
            from_=self.from_number,
            to=to,
            body=body
        )
        return message.sid
    
    async def send_image(self, to: str, image_url: str, caption: Optional[str] = None) -> str:
        """Envia imagem"""
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"
        
        params = {
            "from_": self.from_number,
            "to": to,
            "media_url": [image_url]
        }
        
        if caption:
            params["body"] = caption
        
        message = self.client.messages.create(**params)
        return message.sid
    
    async def send_document(self, to: str, document_url: str, filename: str) -> str:
        """Envia documento (PDF, Excel)"""
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"
        
        message = self.client.messages.create(
            from_=self.from_number,
            to=to,
            media_url=[document_url],
            body=f"📄 {filename}"
        )
        return message.sid
