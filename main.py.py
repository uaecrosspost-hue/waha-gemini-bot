import os
import time
import random
import requests
from urllib.parse import quote
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

WAHA_BASE_URL = os.getenv("WAHA_BASE_URL", "http://localhost:3000")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NETLIFY_BASE_URL = os.getenv("NETLIFY_BASE_URL", "https://premium-coffee-demo.netlify.app/")

NFC_STAND_PHOTO = "static/nfc_stand.jpg"
NFC_DEMO_VIDEO = "static/nfc_demo.mp4"

ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def send_waha_text(chat_id, text):
    url = f"{WAHA_BASE_URL}/api/sendText"
    payload = {"chatId": chat_id, "text": text, "session": "default"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending text: {e}")

def send_waha_file(chat_id, file_path, caption=""):
    url = f"{WAHA_BASE_URL}/api/sendFile"
    payload = {
        "chatId": chat_id,
        "file": {"mimetype": "image/jpeg" if file_path.endswith('.jpg') else "video/mp4", "filename": os.path.basename(file_path)},
        "caption": caption,
        "session": "default"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending file: {e}")

@app.route('/webhook', methods=['POST'])
def waha_webhook():
    data = request.json or {}
    event = data.get('event')
    payload = data.get('payload', {})

    if event != 'message' or payload.get('fromMe', True):
        return jsonify({"status": "ignored"}), 200

    chat_id = payload.get('from')
    user_phone = chat_id.split('@')[0]
    incoming_text = payload.get('body', '')

    business_name = "By Thru Cafe"
    encoded_brand = quote(business_name)
    custom_demo_link = f"{NETLIFY_BASE_URL}?brand={encoded_brand}&phone={user_phone}"

    system_prompt = f"""
    You are a high-level enterprise sales advisor with 10+ years of experience pitching UAE local businesses.
    Context:
    - Target: Local cafes and salons in UAE.
    - Offer: Zero-commission WhatsApp ordering site + FREE physical acrylic NFC Google Review Stand.
    - Demo URL for lead: {custom_demo_link}

    Rules:
    1. Low pressure, high curiosity. Speak like a busy peer advisor.
    2. Keep responses ultra-concise (10-20 words max). Use simple English.
    3. Ask 1 simple question at the end to keep conversation alive.
    4. Link Delivery: Do NOT dump the link immediately. Ask if they want to see it first, or deliver it if they explicitly ask: {custom_demo_link}.
    5. Media Triggers: If asked how the NFC stand looks/works, append '[SEND_NFC_PHOTO]' or '[SEND_NFC_VIDEO]'.
    """

    if not ai_client:
        return jsonify({"error": "Gemini key missing"}), 500

    response = ai_client.models.generate_content(
        model='gemini-1.5-flash',
        contents=incoming_text,
        config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.3)
    )

    reply_text = response.text.strip()
    time.sleep(random.randint(5, 7))

    if '[SEND_NFC_PHOTO]' in reply_text:
        clean_text = reply_text.replace('[SEND_NFC_PHOTO]', '').strip()
        send_waha_text(chat_id, clean_text)
        send_waha_file(chat_id, NFC_STAND_PHOTO, "Here is what the acrylic NFC review stand looks like!")
    elif '[SEND_NFC_VIDEO]' in reply_text:
        clean_text = reply_text.replace('[SEND_NFC_VIDEO]', '').strip()
        send_waha_text(chat_id, clean_text)
        send_waha_file(chat_id, NFC_DEMO_VIDEO, "Here is a quick demo of how it works!")
    else:
        send_waha_text(chat_id, reply_text)

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)