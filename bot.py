import os
import logging
import threading

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]

# Flask server for Render
app = Flask(__name__)


@app.route("/")
def home():
    return "The Speaking English Channel Bot is running! ✅"


@app.route("/health")
def health():
    return "OK"


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📚 Learn English", callback_data="learn"),
            InlineKeyboardButton("🎧 Podcasts", callback_data="podcast"),
        ],
        [
            InlineKeyboardButton("🎬 YouTube Videos", callback_data="videos"),
            InlineKeyboardButton("📖 Vocabulary", callback_data="vocabulary"),
        ],
        [
            InlineKeyboardButton("📝 Grammar Practice", callback_data="grammar"),
            InlineKeyboardButton("🗣️ Speaking Practice", callback_data="speaking"),
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to The Speaking English Channel!\n\n"
        "Improve your English with real-life conversations, "
        "useful expressions, vocabulary, grammar, and speaking practice.\n\n"
        "Choose an option below to get started. 🌟",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    responses = {
        "learn": (
            "📚 Learn English\n\n"
            "Practice practical English for everyday situations.\n\n"
            "New lessons will be added here soon!"
        ),
        "podcast": (
            "🎧 Podcasts\n\n"
            "Listen to The Speaking English Channel "
            "and improve your English through natural conversations."
        ),
        "videos": (
            "🎬 YouTube Videos\n\n"
            "Watch our latest English-learning videos "
            "and practice with Emma and Daniel."
        ),
        "vocabulary": (
            "📖 Vocabulary\n\n"
            "Build your vocabulary with useful everyday English words "
            "and expressions."
        ),
        "grammar": (
            "📝 Grammar Practice\n\n"
            "Practice English grammar with simple explanations "
            "and short exercises."
        ),
        "speaking": (
            "🗣️ Speaking Practice\n\n"
            "Practice speaking English using real-life situations."
        ),
        "about": (
            "ℹ️ About The Speaking English Channel\n\n"
            "We help English learners improve their vocabulary, "
            "grammar, listening, and speaking through practical "
            "English content."
        ),
    }

    await query.edit_message_text(
        responses.get(query.data, "Please choose an option from the menu.")
    )


async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Learn English\n\n"
        "Practice practical English for everyday situations.\n\n"
        "New lessons will be added here soon!"
    )


async def podcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Podcasts\n\n"
        "Listen to The Speaking English Channel "
        "and improve your English through natural conversations."
    )


async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 YouTube Videos\n\n"
        "Watch our latest English-learning videos."
    )


async def vocabulary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Vocabulary\n\n"
        "Build your vocabulary with useful everyday English words "
        "and expressions."
    )


async def grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Grammar Practice\n\n"
        "Practice English grammar with simple explanations "
        "and short exercises."
    )


async def speaking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🗣️ Speaking Practice\n\n"
        "Practice speaking English using real-life situations."
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ About The Speaking English Channel\n\n"
        "Learn English through practical conversations, "
        "vocabulary, grammar, podcasts, and speaking practice."
    )


def main():
    # Start Flask web server for Render
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    # Create Telegram bot
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("learn", learn))
    application.add_handler(CommandHandler("podcast", podcast))
    application.add_handler(CommandHandler("videos", videos))
    application.add_handler(CommandHandler("vocabulary", vocabulary))
    application.add_handler(CommandHandler("grammar", grammar))
    application.add_handler(CommandHandler("speaking", speaking))
    application.add_handler(CommandHandler("about", about))

    application.add_handler(CallbackQueryHandler(button_handler))

    # Start Telegram bot
    application.run_polling()


if __name__ == "__main__":
    main()
