from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError
from collections import defaultdict
from datetime import datetime
import os
import re

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 累積帳本
ledger = defaultdict(int)

# 明細紀錄
records = []

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

        msg = event['message'].get('text', '').strip()
        reply_token = event['replyToken']

        today = datetime.now().strftime("%Y/%m/%d")

        # 格式：
        # 星鋒 +100
        # 彥智 -50
        match = re.match(r"^(.+?)\s*([+-]\d+)$", msg)

        if match:

            name = match.group(1).strip()
            amount = int(match.group(2))

            ledger[name] += amount

            record = f"{today}\n{name} {'+' if amount > 0 else ''}{amount}"

            records.append(record)

            reply = record

        elif msg == "查詢":

            if ledger:

                result = "\n".join(
                    [f"{name}：{money}" for name, money in ledger.items()]
                )

                reply = f"📒 累積帳本\n\n{result}"

            else:
                reply = "目前沒有資料"

        elif msg == "明細":

            if records:

                reply = "\n\n".join(records[-10:])

            else:
                reply = "目前沒有紀錄"

        else:

            reply = (
                "請輸入：\n\n"
                "星鋒 +100\n"
                "彥智 -50\n\n"
                "功能：\n"
                "查詢\n"
                "明細"
            )

        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply)
        )

    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
