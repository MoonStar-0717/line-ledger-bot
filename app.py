from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError
from collections import defaultdict
import os
import re

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 各名稱累積金額
ledger = defaultdict(int)

@app.route("/webhook", methods=["POST"])
def webhook():

    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    data = request.json

    for event in data["events"]:

        if event["type"] != "message":
            continue

        msg = event["message"].get("text", "").strip()
        reply_token = event["replyToken"]

        # 查詢
        if msg == "查詢":

            if not ledger:
                reply = "目前沒有資料"
            else:
                result = "\n".join(
                    [f"{name}：{money}" for name, money in ledger.items()]
                )
                reply = f"📒 累積帳本\n\n{result}"

            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=reply)
            )

        # 記帳
        elif msg.startswith("記帳"):

            content = msg.replace("記帳", "", 1).strip()

            if not content:
                reply = (
                    "請輸入：\n\n"
                    "記帳 星鋒+100\n\n"
                    "或多行：\n"
                    "記帳\n"
                    "星鋒+100\n"
                    "彥智-50"
                )
            else:
                lines = [
                    line.strip()
                    for line in content.splitlines()
                    if line.strip()
                ]

                success = []
                fail = []

                for line in lines:

                    line = (
                        line.replace("＋", "+")
                            .replace("－", "-")
                            .replace("　", " ")
                    )

                    match = re.match(
                        r"^(.+?)\s*([+-]\s*\d+)$",
                        line
                    )

                    if match:
                        name = match.group(1).strip()
                        amount = int(match.group(2).replace(" ", ""))

                        ledger[name] += amount

                        success.append(
                            f"{name} "
                            f"{'+' if amount > 0 else ''}{amount}"
                            f"｜累積：{ledger[name]}"
                        )
                    else:
                        fail.append(line)

                if fail:
                    reply = "格式錯誤請重新輸入"
                elif success:
                    reply = "已更新：\n" + "\n".join(success)
                else:
                    reply = "格式錯誤請重新輸入"

            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=reply)
            )

        # 其他聊天不回覆
        else:
            pass

    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
