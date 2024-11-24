import os
import asyncio
import json
import requests
from google.auth import default
from google.cloud import secretmanager
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, request, abort

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
        response.raise_for_status()
        response_data = response.json()

        # Handle response
        if "answer" in response_data:
            reply = f"Answer: {response_data['answer']}"
        elif "error" in response_data:
            reply = f"Error: {response_data['error']}"
        else:
            reply = "Unexpected response from the API."
    except requests.exceptions.RequestException as e:
        reply = f"Error contacting the API: {e}"
    except Exception as e:
        reply = f"An unexpected error occurred: {e}"

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
        # Validate the request is from Telegram (basic security)
        if not json_data.get("update_id"):
            abort(403)

        update = Update.de_json(json_data, bot)
        asyncio.run(application.process_update(update))
        return '', 200
    except Exception as e:
        app.logger.error(f"Error processing webhook: {e}")
        abort(500)

async def set_webhook():
    try:
        webhook_url = os.getenv("WEBHOOK_URL")
        if not webhook_url:
            raise ValueError("WEBHOOK_URL environment variable is not set.")
        await bot.set_webhook(webhook_url + "/webhook")
        app.logger.info(f"Webhook successfully set to {webhook_url}/webhook")
    except Exception as e:
        app.logger.error(f"Error setting webhook: {e}")

def main():
    try:
        asyncio.run(set_webhook())
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
    except Exception as e:
        app.logger.error(f"Failed to start application: {e}")


if __name__ == "__main__":
    main()