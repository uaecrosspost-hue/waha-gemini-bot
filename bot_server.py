import base64
import os
from fastapi import FastAPI, Request
import httpx
from google import genai

app = FastAPI()

WAHA_URL = os.getenv("WAHA_URL", "https://waha-production-f493.up.railway.app")
WAHA_API_KEY = os.getenv("WHATSAPP_API_KEY", "d6f6d569098f45be99424cd8cd849c4a")
SWAGGER_USER = os.getenv("WHATSAPP_SWAGGER_USER", "admin")
DASHBOARD_PASS = os.getenv("WHATSAPP_SWAGGER_PASSWORD", "d60c3f1a35ad48f895e0e9834eb1cafc")

client = genai.Client()

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    event = data.get("event")
    
    if event == "message.any":
        payload = data.get("payload", {})
        from_me = payload.get("fromMe", False)
        
        if not from_me:
            chat_id = payload.get("from")
            text = payload.get("body", "")
            
            # Non-blocking async call to Gemini API
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"You are a sales assistant for a UAE specialty coffee business. Reply to this customer message concisely: {text}"
            )
            reply_text = response.text

            # Encode Basic Auth required by Railway WAHA
            auth_str = base64.b64encode(f"{SWAGGER_USER}:{DASHBOARD_PASS}".encode("utf-8")).decode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": WAHA_API_KEY,
                "Authorization": f"Basic {auth_str}"
            }

            async with httpx.AsyncClient() as http_client:
                await http_client.post(
                    f"{WAHA_URL}/api/sendText",
                    headers=headers,
                    json={
                        "session": "default",
                        "chatId": chat_id,
                        "text": reply_text
                    }
                )
    return {"status": "ok"}
