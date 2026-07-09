import os
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage

app = FastAPI()

# 從 Render 後台的環境變數讀取金鑰，確保安全
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

@handler.add(TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text = f"🤖 [雲端助理] 您好！我已收到您的指令：'{user_message}'。\n目前本地主機已安心關機，雲端高可用度運行中！"
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )