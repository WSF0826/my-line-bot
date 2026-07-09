import os
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent

app = FastAPI()

# 讀取雲端環境變數
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
    reply_text = f"🤖 [雲端助理] 您好！我已收到您的指令：'{user_message}'。\n目前本地主機已安心關機，雲端高可用度運行中！"
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        # ✨ 終極修正：改用最標準、不堵塞的 reply_message 進行發射
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
