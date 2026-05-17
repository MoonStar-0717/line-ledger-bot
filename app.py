from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError
from collections import defaultdict
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

ledger = defaultdict(int)

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400

    data = request.json

    for event in data['events']:
        if event['type'] != 'message':
            continue

        msg = event['message'].get('text', '')
        reply_token = event['replyToken']
        user_name = "群友"

        if msg.startswith('+'):
            amount = int(msg[1:])
            ledger[user_name] += amount
            reply = f"{user_name} +{amount}\n目前餘額：{ledger[user_name]}"

        elif msg.startswith('-'):
            amount = int(msg[1:])
            ledger[user_name] -= amount
            reply = f"{user_name} -{amount}\n目前餘額：{ledger[user_name]}"

        elif msg == '查詢':
            total = "\n".join(
                [f"{k}：{v}" for k, v in ledger.items()]
            )
            reply = f"📒 帳本\n\n{total}"

        else:
            reply = "輸入 +100 或 -100 或 查詢"

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply)
        )

    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
