import os
from fastapi import FastAPI, Request
import httpx
from google import genai

app = FastAPI()

WAHA_URL = "https://waha-production-f493.up.railway.app"
WAHA_API_KEY = "d6f6d569098f45be99424cd8cd849c4a"
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
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"You are a sales assistant for a UAE specialty coffee business. Reply to this customer message concisely: {text}"
            )
            reply_text = response.text

            async with httpx.AsyncClient() as http_client:
                await http_client.post(
                    f"{WAHA_URL}/api/sendText",
                    headers={"X-Api-Key": WAHA_API_KEY},
                    json={
                        "session": "default",
                        "chatId": chat_id,
                        "text": reply_text
                    }
                )
    return {"status": "ok"}
