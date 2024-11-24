import os
import json
import asyncio
import requests
from google.auth import default
from google.cloud import secretmanager
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, request


app = Flask(__name__)

project_id = default()[1]

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


bot_token = get_secret("BOT_TOKEN")
bot = Bot(token=bot_token)
application = Application.builder().token(bot_token).build()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text.strip()

    if "|" not in user_message:
        await update.message.reply_text(
            "Please provide input in the format: 'Context | Question'\nExample:\n"
            "The Transformers library provides NLP tools. | What does it provide?"
        )
        return

    context_text, question = map(str.strip, user_message.split("|", 1))
    api_url = os.getenv("API_URL") + '/answer'
    payload = {"context": context_text, "question": question}

    try:
        response = requests.post(api_url, json=payload)
    except Exception as e:
        await update.message.reply_text(f"An unexpected error occurred: {str(e)}")
        return

    reply = "Sorry, something went wrong. Please try again."
    if response.status_code == 200:
        response = response.json()
        if "answer" in response:
            reply = f"Answer: {response['answer']}"
        elif "error" in response:
            reply = f"Error: {response['error']}"
    await update.message.reply_text(reply)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello! I'm a Question Answering Bot. Send me a message in the format:\n\n"
        "Context | Question\n\nExample:\n"
        "The Transformers library provides NLP tools. | What does it provide?"
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = json.loads(request.get_data().decode('UTF-8'))
        print(f"Incoming webhook payload: {json_data}")
        update = Update.de_json(json_data, bot)
        asyncio.run(application.process_update(update))
        return '', 200
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return '', 500

async def set_webhook():
    url = os.getenv("WEBHOOK_URL")
    await bot.set_webhook(url + "/webhook")

def main():
    asyncio.run(set_webhook())
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()