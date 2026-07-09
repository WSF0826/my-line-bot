import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent

app = FastAPI()

# 讀取環境變數
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
openrouter_api_key = os.getenv('OPENROUTER_API_KEY')

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)


# ─────────────────────────────────────────
# 指令處理（以 / 開頭）
# ─────────────────────────────────────────
def handle_command(command: str) -> str:
    if command == "/help":
        return (
            "📋 可用指令：\n"
            "/help  — 顯示此說明\n"
            "/about — 關於這個機器人\n"
            "/time  — 顯示目前時間\n"
            "（其他訊息會由 AI 回覆）"
        )
    elif command == "/about":
        return "🤖 我是由 OpenRouter AI 驅動的智慧助理！"
    elif command == "/time":
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return f"🕐 台灣時間：{now}"
    else:
        return f"❓ 未知指令：{command}\n輸入 /help 查看可用指令。"


# ─────────────────────────────────────────
# AI 回覆（送給 OpenRouter）
# ─────────────────────────────────────────
def ask_openrouter(user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",  # 免費模型
        "messages": [
            {
                "role": "system",
                "content": "你是一個親切的繁體中文助理，用簡潔自然的口語回覆，回覆長度控制在100字以內。"
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    }

    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ AI 暫時無法回應，請稍後再試。（{str(e)[:50]}）"


# ─────────────────────────────────────────
# Webhook 接收
# ─────────────────────────────────────────
@app.post("/webhook")
async def handle_callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    body_str = body.decode('utf-8')
    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return 'OK'


@handler.add(MessageEvent)
def handle_message(event):
    if not hasattr(event.message, 'text'):
        return  # 非文字訊息略過

    user_msg = event.message.text.strip()

    # 判斷是指令還是 AI 對話
    if user_msg.startswith("/"):
        reply_text = handle_command(user_msg)
    else:
        reply_text = ask_openrouter(user_msg)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
