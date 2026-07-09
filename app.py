import os
import sys
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent

app = FastAPI()

channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text = f"🤖 [雲端助理] 您好！我已收到您的指令：'{user_message}'。\n目前雲端高可用度完美運行中！"
    
    print(f"--- 開始處理訊息，準備回覆 Token: {event.reply_token} ---", flush=True)
    
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        print("--- 🟢 訊息發射成功！已成功送回 LINE 伺服器 ---", flush=True)
    except Exception as e:
        # 💥 關鍵抓漏：如果發射失敗，會直接在 Render Logs 印出真正的原因！
        print(f"--- ❌ 訊息發射失敗！錯誤原因: {str(e)} ---", flush=True)
