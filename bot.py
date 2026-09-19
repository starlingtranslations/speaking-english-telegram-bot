import os
import random
import threading
import requests

from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")

PORT = int(os.environ.get("PORT", 10000))


# ============================================================
# CHECK ENVIRONMENT VARIABLES
# ============================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing from Render Environment Variables.")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing from Render Environment Variables.")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError(
        "SUPABASE_SECRET_KEY is missing from Render Environment Variables."
    )


# ============================================================
# SUPABASE SETTINGS
# ============================================================

SUPABASE_HEADERS = {
    "apikey": SUPABASE_SECRET_KEY,
    "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
    "Content-Type": "application/json",
}


# ============================================================
# FLASK SERVER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "The Speaking English Channel Bot is running! 🗣️"


@app.route("/health")
def health():
    return "OK"


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
    )


# ============================================================
# SUPABASE VOCABULARY
# ============================================================

def get_random_vocabulary():
    """Get a random vocabulary word from Supabase."""

    url = f"{SUPABASE_URL}/rest/v1/vocabulary"

    params = {
        "select": "id,word,level,meaning,example,category,synonyms,antonyms",
        "limit": "1000",
    }

    try:
        response = requests.get(
            url,
            headers=SUPABASE_HEADERS,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        words = response.json()

        if not words:
            return None

        return random.choice(words)

    except Exception as error:
        print(f"Supabase vocabulary error: {error}")
        return None


# ============================================================
# MAIN MENU
# ============================================================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📚 Learn English", callback_data="learn"),
            InlineKeyboardButton("🎧 Podcasts", callback_data="podcasts"),
        ],
        [
            InlineKeyboardButton("🎬 YouTube Videos", callback_data="youtube"),
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

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# START COMMAND
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "👋 <b>Welcome to The Speaking English Channel!</b>\n\n"
        "🌟 Improve your English with real-life conversations, "
        "useful expressions, vocabulary, grammar, podcasts, "
        "and speaking practice.\n\n"
        "📚 Learn English\n"
        "🗣️ Speak English\n"
        "💪 Speak with confidence!\n\n"
        "Choose an option below:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ============================================================
# LEARN COMMAND
# ============================================================

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📚 <b>Learn English</b>\n\n"
        "Choose what you want to practice:\n\n"
        "🗣️ Everyday English\n"
        "📖 Vocabulary\n"
        "📝 Grammar\n"
        "💬 Speaking\n\n"
        "More lessons are coming soon! 🌟",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ============================================================
# PODCAST COMMAND
# ============================================================

async def podcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎧 <b>English Podcasts</b>\n\n"
        "Listen to natural English conversations with "
        "Emma and Daniel.\n\n"
        "🎙️ Real-life English\n"
        "📚 Useful vocabulary\n"
        "🗣️ Speaking practice\n\n"
        "New episodes are coming soon!",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ============================================================
# YOUTUBE COMMAND
# ============================================================

async def youtube_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "▶️ Open YouTube Channel",
                url="https://youtube.com/@thespeakingenglishchannel",
            )
        ],
        [
            InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")
        ],
    ]

    await update.message.reply_text(
        "🎬 <b>The Speaking English Channel</b>\n\n"
        "Watch our English-learning videos, Shorts, "
        "podcasts and speaking practice.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# VOCABULARY COMMAND
# ============================================================

async def vocabulary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    word = get_random_vocabulary()

    if not word:
        await update.message.reply_text(
            "📖 <b>Vocabulary</b>\n\n"
            "I couldn't find any vocabulary in the database yet.\n\n"
            "Please add some words to the Supabase "
            "<b>vocabulary</b> table.",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )
        return

    await send_vocabulary(update, word)


# ============================================================
# SEND VOCABULARY
# ============================================================

async def send_vocabulary(update_or_query, word):

    word_text = word.get("word", "Unknown")
    level = word.get("level") or "All Levels"
    meaning = word.get("meaning") or "Meaning not available."
    example = word.get("example") or "Example not available."
    category = word.get("category") or "General"
    synonyms = word.get("synonyms") or "None"
    antonyms = word.get("antonyms") or "None"

    text = (
        f"📖 <b>Daily Vocabulary</b>\n\n"
        f"🌟 <b>{word_text}</b>\n\n"
        f"📊 <b>Level:</b> {level}\n"
        f"🏷️ <b>Category:</b> {category}\n\n"
        f"💡 <b>Meaning:</b>\n{meaning}\n\n"
        f"💬 <b>Example:</b>\n"
        f"“{example}”\n\n"
        f"🔹 <b>Synonyms:</b> {synonyms}\n"
        f"🔸 <b>Antonyms:</b> {antonyms}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 New Word",
                callback_data="new_word",
            )
        ],
        [
            InlineKeyboardButton(
                "🎯 Vocabulary Quiz",
                callback_data="vocab_quiz",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Main Menu",
                callback_data="main_menu",
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update_or_query, "callback_query") and update_or_query.callback_query:
        await update_or_query.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    else:
        await update_or_query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


# ============================================================
# VOCABULARY QUIZ
# ============================================================

async def vocabulary_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):

    word = get_random_vocabulary()

    if not word:
        await update.callback_query.edit_message_text(
            "❌ I couldn't load a vocabulary word right now.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Menu",
                            callback_data="main_menu",
                        )
                    ]
                ]
            ),
        )
        return

    correct_meaning = word.get("meaning") or "Meaning unavailable."

    all_words = []

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/vocabulary",
            headers=SUPABASE_HEADERS,
            params={
                "select": "meaning",
                "limit": "100",
            },
            timeout=10,
        )

        response.raise_for_status()
        all_words = response.json()

    except Exception as error:
        print(f"Quiz error: {error}")

    meanings = [
        item.get("meaning")
        for item in all_words
        if item.get("meaning") and item.get("meaning") != correct_meaning
    ]

    meanings = list(dict.fromkeys(meanings))

    random.shuffle(meanings)

    options = meanings[:3]
    options.append(correct_meaning)

    random.shuffle(options)

    context.user_data["quiz_correct"] = correct_meaning
    context.user_data["quiz_word"] = word.get("word", "Unknown")

    keyboard = []

    for option in options:
        keyboard.append(
            [
                InlineKeyboardButton(
                    option[:60],
                    callback_data=f"quiz:{option}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Main Menu",
                callback_data="main_menu",
            )
        ]
    )

    await update.callback_query.edit_message_text(
        f"🎯 <b>Vocabulary Quiz</b>\n\n"
        f"What is the meaning of:\n\n"
        f"🌟 <b>{word.get('word', 'Unknown')}</b>?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# BUTTON HANDLER
# ============================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # Main menu
    if data == "main_menu":

        await query.edit_message_text(
            "🏠 <b>Main Menu</b>\n\n"
            "What would you like to do?",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )
        return

    # Learn English
    if data == "learn":

        await query.edit_message_text(
            "📚 <b>Learn English</b>\n\n"
            "Learn English through:\n\n"
            "🗣️ Real-life conversations\n"
            "📖 Vocabulary\n"
            "📝 Grammar\n"
            "🎧 Listening\n"
            "💬 Speaking practice\n\n"
            "More lessons are coming soon! 🌟",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📖 Vocabulary",
                            callback_data="vocabulary",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📝 Grammar",
                            callback_data="grammar",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🗣️ Speaking",
                            callback_data="speaking",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Menu",
                            callback_data="main_menu",
                        )
                    ],
                ]
            ),
        )
        return

    # Podcasts
    if data == "podcasts":

        await query.edit_message_text(
            "🎧 <b>English Podcasts</b>\n\n"
            "Listen to natural conversations with Emma and Daniel.\n\n"
            "🎙️ Real-life English\n"
            "📚 Vocabulary\n"
            "💬 Useful expressions\n"
            "🗣️ Speaking practice\n\n"
            "New episodes are coming soon!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🎬 YouTube",
                            url="https://youtube.com/@thespeakingenglishchannel",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Menu",
                            callback_data="main_menu",
                        )
                    ],
                ]
            ),
        )
        return

    # YouTube
    if data == "youtube":

        await query.edit_message_text(
            "🎬 <b>The Speaking English Channel</b>\n\n"
            "Watch our latest English-learning videos and Shorts.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "▶️ Open YouTube",
                            url="https://youtube.com/@thespeakingenglishchannel",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Menu",
                            callback_data="main_menu",
                        )
                    ],
                ]
            ),
        )
        return

    # Vocabulary
    if data == "vocabulary":

        word = get_random_vocabulary()

        if not word:
            await query.edit_message_text(
                "📖 <b>Vocabulary</b>\n\n"
                "There are no vocabulary words in Supabase yet.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Main Menu",
                                callback_data="main_menu",
                            )
                        ]
                    ]
                ),
            )
            return

        await send_vocabulary(update, word)
        return

    # New vocabulary word
    if data == "new_word":

        word = get_random_vocabulary()

        if not word:
            await query.edit_message_text(
                "❌ No vocabulary words found in Supabase.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Main Menu",
                                callback_data="main_menu",
                            )
                        ]
                    ]
                ),
            )
            return

        await send_vocabulary(update, word)
        return

    # Vocabulary quiz
    if data == "vocab_quiz":

        await vocabulary_quiz(update, context)
        return

    # Quiz answer
    if data.startswith("quiz:"):

        selected_answer = data[5:]
        correct_answer = context.user_data.get("quiz_correct")
        quiz_word = context.user_data.get("quiz_word", "this word")

        if selected_answer == correct_answer:

            text = (
                "🎉 <b>Correct!</b>\n\n"
                f"🌟 <b>{quiz_word}</b>\n\n"
                f"💡 {correct_answer}"
            )

        else:

            text = (
                "❌ <b>Not quite!</b>\n\n"
                f"🌟 <b>{quiz_word}</b>\n\n"
                f"✅ <b>Correct answer:</b>\n{correct_answer}"
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎯 Another Quiz",
                    callback_data="vocab_quiz",
                )
            ],
            [
                InlineKeyboardButton(
                    "📖 New Word",
                    callback_data="new_word",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Main Menu",
                    callback_data="main_menu",
                )
            ],
        ]

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # Grammar
    if data == "grammar":

        await query.edit_message_text(
            "📝 <b>Grammar Practice</b>\n\n"
            "Grammar lessons and interactive exercises "
            "will be added here soon. 📚",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Menu",
                            callback_data="main_menu",
                        )
                    ]
                ]
            ),
        )
        return

    # Speaking
    if data == "speaking":

        await query.edit_message_text(
            "🗣️ <b>Speaking Practice</b>\n\n"
            "Practice useful English conversations "
            "and improve your confidence.\n\n"
            "Speaking activities are coming soon! 🎙️",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Menu",
                            callback_data="main_menu",
                        )
                    ]
                ]
            ),
        )
        return

    # About
    if data == "about":

        await query.edit_message_text(
            "ℹ️ <b>About The Speaking English Channel</b>\n\n"
            "Learn English with real-life conversations, "
            "vocabulary, grammar, podcasts and speaking practice.\n\n"
            "🌟 Learn English.\n"
            "🗣️ Speak English.\n"
            "💪 Speak with confidence.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "▶️ YouTube Channel",
                            url="https://youtube.com/@thespeakingenglishchannel",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Main Menu",
                            callback_data="main_menu",
                        )
                    ],
                ]
            ),
        )
        return


# ============================================================
# COMMANDS
# ============================================================

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "ℹ️ <b>About The Speaking English Channel</b>\n\n"
        "Learn English with real-life conversations, "
        "vocabulary, grammar, podcasts and speaking practice.\n\n"
        "🌟 Learn English.\n"
        "🗣️ Speak English.\n"
        "💪 Speak with confidence.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ============================================================
# START BOT
# ============================================================

def main():

    # Start Flask health server in the background
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
    )

    flask_thread.start()

    print("Flask server started.")
    print("Starting Telegram bot...")

    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("podcast", podcast_command))
    application.add_handler(CommandHandler("videos", youtube_command))
    application.add_handler(CommandHandler("vocabulary", vocabulary_command))
    application.add_handler(CommandHandler("grammar", learn_command))
    application.add_handler(CommandHandler("speaking", learn_command))
    application.add_handler(CommandHandler("about", about_command))

    # Buttons
    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("Telegram bot is running!")

    application.run_polling(
        drop_pending_updates=True
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
