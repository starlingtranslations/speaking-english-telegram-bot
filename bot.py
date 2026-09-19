import os
import logging
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
            "Build your
