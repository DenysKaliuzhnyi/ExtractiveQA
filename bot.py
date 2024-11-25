import os
import asyncio
import logging
import aiohttp
from google.auth import default
from google.cloud import secretmanager
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
api_url = os.getenv("API_URL")
project_id = default()[1]


def get_secret(secret_name: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not api_url:
        logger.error("API_URL environment variable is not set")
        await update.message.reply_text("Bot configuration error. Please contact administrator.")
        return

    user_message = update.message.text.strip()

    if "|" not in user_message:
        await update.message.reply_text(
            "Please provide input in the format: 'Context | Question'\nExample:\n"
            "The Transformers library provides NLP tools. | What does it provide?"
        )
        return

    context_text, question = map(str.strip, user_message.split("|", 1))
    payload = {"context": context_text, "question": question}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(f"{os.getenv('API_URL')}/answer", json=payload) as response:
                response_data = await response.json()
                if response.status != 200:
                    logger.error(f"API error: {response.status} - {response_data}")
                    raise aiohttp.ClientError(f"API returned status {response.status}")
                reply = response_data.get('answer') or response_data.get('error', 'Internal QA model error.')
    except aiohttp.ClientError as e:
        logger.error(f"API request failed: {e}")
        reply = "Sorry, I'm having trouble reaching the API. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        reply = "An unexpected error occurred. Please try again later."

    await update.message.reply_text(reply)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello! I'm a Question Answering Bot. Send me a message in the format:\n\n"
        "Context | Question\n\nExample:\n"
        "The Transformers library provides NLP tools. | What does it provide?"
    )


def main() -> None:
    try:
        bot_token = get_secret("BOT_TOKEN")
        webhook_url = os.getenv("WEBHOOK_URL")
        port = int(os.getenv("PORT", "8080"))

        if not webhook_url:
            raise ValueError("WEBHOOK_URL environment variable is not set")

        application = Application.builder().token(bot_token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info(f"Starting bot webhook on port {port}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="/webhook",
            webhook_url=f"{webhook_url}/webhook"
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()