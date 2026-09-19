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

# Render web server
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


# =========================
# START MENU
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("📚 Learn English", callback_data="learn"),
            InlineKeyboardButton("🎧 Podcasts", callback_data="podcast"),
        ],
        [
            InlineKeyboardButton(
                "🎬 YouTube Videos",
                callback_data="videos"
            ),
            InlineKeyboardButton(
                "📖 Vocabulary",
                callback_data="vocabulary"
            ),
        ],
        [
            InlineKeyboardButton(
                "📝 Grammar Practice",
                callback_data="grammar"
            ),
            InlineKeyboardButton(
                "🗣️ Speaking Practice",
                callback_data="speaking"
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ About",
                callback_data="about"
            ),
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


# =========================
# BUTTONS
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    # YouTube
    if query.data == "videos":

        keyboard = [
            [
                InlineKeyboardButton(
                    "▶️ Open YouTube Channel",
                    url="https://youtube.com/@thespeakingenglishchannel"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Menu",
                    callback_data="back"
                )
            ],
        ]

        await query.edit_message_text(
            "🎬 YouTube Videos\n\n"
            "Watch The Speaking English Channel on YouTube "
            "and improve your English through practical lessons, "
            "real-life conversations, vocabulary, grammar, "
            "and speaking practice.\n\n"
            "Tap below to visit our YouTube channel. 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return

    # Back to Menu
    if query.data == "back":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📚 Learn English",
                    callback_data="learn"
                ),
                InlineKeyboardButton(
                    "🎧 Podcasts",
                    callback_data="podcast"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎬 YouTube Videos",
                    callback_data="videos"
                ),
                InlineKeyboardButton(
                    "📖 Vocabulary",
                    callback_data="vocabulary"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📝 Grammar Practice",
                    callback_data="grammar"
                ),
                InlineKeyboardButton(
                    "🗣️ Speaking Practice",
                    callback_data="speaking"
                ),
            ],
            [
                InlineKeyboardButton(
                    "ℹ️ About",
                    callback_data="about"
                ),
            ],
        ]

        await query.edit_message_text(
            "👋 Welcome to The Speaking English Channel!\n\n"
            "Improve your English with real-life conversations, "
            "useful expressions, vocabulary, grammar, and speaking practice.\n\n"
            "Choose an option below to get started. 🌟",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return

    # Other sections
    responses = {

        "learn": (
            "📚 Learn English\n\n"
            "Learn practical English for everyday situations.\n\n"
            "New lessons will be added here soon! 🌟"
        ),

        "podcast": (
            "🎧 Podcasts\n\n"
            "Listen to The Speaking English Channel "
            "and improve your English through natural conversations.\n\n"
            "Podcast episodes will be added here soon! 🎙️"
        ),

        "vocabulary": (
            "📖 Vocabulary\n\n"
            "Build your vocabulary with useful everyday "
            "English words and expressions.\n\n"
            "Vocabulary practice will be added here soon! 📚"
        ),

        "grammar": (
            "📝 Grammar Practice\n\n"
            "Practice English grammar with simple explanations "
            "and short exercises.\n\n"
            "Grammar exercises will be added here soon! ✏️"
        ),

        "speaking": (
            "🗣️ Speaking Practice\n\n"
            "Practice speaking English using real-life situations.\n\n"
            "Interactive speaking practice will be added here soon! 🎤"
        ),

        "about": (
            "ℹ️ About The Speaking English Channel\n\n"
            "The Speaking English Channel helps English learners "
            "improve their vocabulary, grammar, listening, "
            "speaking, and everyday communication skills.\n\n"
            "Learn English. Speak English. "
            "Speak with confidence. 🗣️"
        ),
    }

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Back to Menu",
                callback_data="back"
            )
        ]
    ]

    await query.edit_message_text(
        responses.get(
            query.data,
            "Please choose an option from the menu."
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# COMMANDS
# =========================

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📚 Learn English\n\n"
        "Learn practical English for everyday situations.\n\n"
        "New lessons will be added here soon! 🌟"
    )


async def podcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎧 Podcasts\n\n"
        "Listen to The Speaking English Channel "
        "and improve your English through natural conversations."
    )


async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "▶️ Open YouTube Channel",
                url="https://youtube.com/@thespeakingenglishchannel"
            )
        ]
    ]

    await update.message.reply_text(
        "🎬 Watch The Speaking English Channel on YouTube! 🎬\n\n"
        "Improve your English with practical lessons, "
        "real-life conversations, vocabulary, grammar, "
        "and speaking practice.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def vocabulary(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📖 Vocabulary\n\n"
        "Build your vocabulary with useful everyday "
        "English words and expressions."
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
