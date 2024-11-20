import os
import requests
from google.cloud import secretmanager
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters


project_id = os.getenv("GCP_PROJECT_ID")

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text.strip()

    if "|" not in user_message:
        await update.message.reply_text(
            "Please provide input in the format: 'Context | Question'\nExample:\n"
            "The Transformers library provides NLP tools. | What does it provide?"
        )
        return

    context_text, question = map(str.strip, user_message.split("|", 1))
    api_url = "http://localhost:8000/answer"
    payload = {"context": context_text, "question": question}
    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        answer = response.json().get("answer", "Sorry, I couldn't find an answer.")
        await update.message.reply_text(f"Answer: {answer}")
    else:
        await update.message.reply_text("Sorry, something went wrong. Please try again.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello! I'm a Question Answering Bot. Send me a message in the format:\n\n"
        "Context | Question\n\nExample:\n"
        "The Transformers library provides NLP tools. | What does it provide?"
    )


def main():
    bot_token = get_secret("BOT_TOKEN")

    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == "__main__":
    main()
    