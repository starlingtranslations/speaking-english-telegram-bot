import os
import random
import threading
import html
import requests

from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
# THE SPEAKING ENGLISH CHANNEL BOT
# Supabase-powered learning bot
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")
PORT = int(os.environ.get("PORT", 10000))

YOUTUBE_URL = "https://youtube.com/@thespeakingenglishchannel"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing from Render Environment Variables.")
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing from Render Environment Variables.")
if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY is missing from Render Environment Variables.")

app = Flask(__name__)


@app.get("/")
def home():
    return "The Speaking English Channel Bot is running."


@app.get("/health")
def health():
    return "OK"


def run_flask():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


# ============================================================
# SUPABASE
# ============================================================

def supabase_headers():
    return {
        "apikey": SUPABASE_SECRET_KEY,
        "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def supabase_get(table, select="*", params=None, limit=100):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    query = {"select": select, "limit": str(limit)}
    if params:
        query.update({k: str(v) for k, v in params.items() if v is not None})

    response = requests.get(
        url,
        headers=supabase_headers(),
        params=query,
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else []


def clean(value, fallback="Not available."):
    if value is None or str(value).strip() == "":
        return fallback
    return str(value).strip()


def esc(value, fallback="Not available."):
    return html.escape(clean(value, fallback))


def random_rows(rows, count):
    if not rows:
        return []
    if len(rows) <= count:
        return rows[:]
    return random.sample(rows, count)


# ============================================================
# TELEGRAM UI
# ============================================================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Learn English", callback_data="learn")],
        [InlineKeyboardButton("🎧 Podcasts", callback_data="podcasts"),
         InlineKeyboardButton("🎬 YouTube Videos", callback_data="videos")],
        [InlineKeyboardButton("📖 Vocabulary", callback_data="vocabulary")],
        [InlineKeyboardButton("📝 Grammar Practice", callback_data="grammar")],
        [InlineKeyboardButton("🗣️ Speaking Practice", callback_data="speaking")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")],
    ])


def back_button(callback="main_menu"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=callback)],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])


def level_keyboard(prefix, include_mixed=False):
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    rows = []
    for i in range(0, len(levels), 2):
        row = []
        for level in levels[i:i + 2]:
            row.append(InlineKeyboardButton(level, callback_data=f"{prefix}:{level}"))
        rows.append(row)
    if include_mixed:
        rows.append([InlineKeyboardButton("🎲 Mixed Level", callback_data=f"{prefix}:MIXED")])
    rows.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


def level_name(level):
    return "Mixed Level" if level == "MIXED" else f"Level {level}"


async def send_or_edit(update, text, reply_markup=None, parse_mode="HTML"):
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )


# ============================================================
# START / MAIN MENU
# ============================================================

WELCOME = (
    "🌟 <b>Welcome to The Speaking English Channel!</b>\n\n"
    "Improve your English with real-life conversations, useful expressions, "
    "vocabulary, grammar, podcasts, and speaking practice.\n\n"
    "Choose what you want to practise:"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(WELCOME, reply_markup=main_menu(), parse_mode="HTML")


# ============================================================
# LEARN ENGLISH
# ============================================================

async def show_learn(update_or_query):
    text = (
        "📚 <b>Learn English</b>\n\n"
        "Choose your English level. Lessons are loaded from the Supabase "
        "<code>lessons</code> table."
    )
    await send_or_edit(update_or_query, text, level_keyboard("lesson"))


async def show_level_lessons(update_or_query, level):
    try:
        rows = supabase_get(
            "lessons",
            params={
                "level": f"eq.{level}",
                "published": "eq.true",
                "order": "sort_order.asc",
            },
            limit=50,
        )
    except Exception:
        rows = []

    if not rows:
        await send_or_edit(
            update_or_query,
            f"📚 <b>{esc(level_name(level))}</b>\n\n"
            "No lessons have been added for this level yet.\n\n"
            "Add lessons to the Supabase <code>lessons</code> table and they will appear here.",
            back_button("learn"),
        )
        return

    buttons = []
    for row in rows:
        buttons.append([
            InlineKeyboardButton(
                f"📖 {clean(row.get('title'), 'Untitled lesson')[:45]}",
                callback_data=f"lessonview:{row.get('id')}",
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Levels", callback_data="learn")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    await send_or_edit(
        update_or_query,
        f"📚 <b>{esc(level_name(level))}</b>\n\nChoose a lesson:",
        InlineKeyboardMarkup(buttons),
    )


async def show_lesson(update_or_query, lesson_id):
    try:
        rows = supabase_get(
            "lessons",
            params={"id": f"eq.{lesson_id}"},
            limit=1,
        )
        lesson = rows[0] if rows else None
    except Exception:
        lesson = None

    if not lesson:
        await send_or_edit(update_or_query, "The lesson could not be found.", back_button("learn"))
        return

    level = clean(lesson.get("level"), "")
    title = esc(lesson.get("title"), "Lesson")
    topic = esc(lesson.get("topic"), "")
    content = esc(lesson.get("content"), "Lesson content is not available.")
    vocabulary = esc(lesson.get("vocabulary"), "")
    grammar = esc(lesson.get("grammar_focus"), "")
    exercise = esc(lesson.get("exercise"), "")

    parts = [f"📖 <b>{title}</b>"]
    if topic:
        parts.append(f"<i>{topic}</i>")
    if level:
        parts.append(f"🎯 <b>Level:</b> {esc(level)}")
    parts.append("")
    parts.append(content)

    if vocabulary:
        parts.extend(["", "🧠 <b>Key Vocabulary</b>", vocabulary])
    if grammar:
        parts.extend(["", "📝 <b>Grammar Focus</b>", grammar])
    if exercise:
        parts.extend(["", "✏️ <b>Practice</b>", exercise])

    buttons = [
        [InlineKeyboardButton("🔙 Lessons", callback_data=f"lesson:{level}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    await send_or_edit(update_or_query, "\n".join(parts), InlineKeyboardMarkup(buttons))


# ============================================================
# PODCASTS / YOUTUBE
# ============================================================

async def show_podcasts(update_or_query):
    try:
        rows = supabase_get(
            "podcasts",
            params={"published": "eq.true", "order": "sort_order.asc"},
            limit=50,
        )
    except Exception:
        rows = []

    buttons = []
    for row in rows:
        url = clean(row.get("url"), "")
        if url:
            buttons.append([InlineKeyboardButton(
                f"🎧 {clean(row.get('title'), 'Podcast')[:50]}",
                url=url
            )])

    text = (
        "🎧 <b>Podcasts</b>\n\n"
        "Listen to English-learning episodes from The Speaking English Channel."
    )

    if not rows:
        text += "\n\nNo podcast episodes have been added to Supabase yet."

    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    await send_or_edit(update_or_query, text, InlineKeyboardMarkup(buttons))


async def show_videos(update_or_query):
    try:
        rows = supabase_get(
            "videos",
            params={"published": "eq.true", "order": "sort_order.asc"},
            limit=50,
        )
    except Exception:
        rows = []

    buttons = []
    for row in rows:
        url = clean(row.get("url"), "")
        if url:
            buttons.append([InlineKeyboardButton(
                f"🎬 {clean(row.get('title'), 'Video')[:50]}",
                url=url
            )])

    if not rows:
        buttons.append([InlineKeyboardButton("▶️ Open YouTube Channel", url=YOUTUBE_URL)])

    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    text = (
        "🎬 <b>YouTube Videos</b>\n\n"
        "Watch English-learning videos from The Speaking English Channel."
    )
    if not rows:
        text += "\n\nNo individual videos have been added to Supabase yet."

    await send_or_edit(update_or_query, text, InlineKeyboardMarkup(buttons))


# ============================================================
# VOCABULARY
# ============================================================

async def show_vocabulary_menu(update_or_query):
    text = (
        "📖 <b>Vocabulary Practice</b>\n\n"
        "Your vocabulary comes from the Supabase <code>vocabulary</code> table.\n"
        "Choose a practice mode:"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Random Word", callback_data="vocab_random")],
        [InlineKeyboardButton("📚 Word by Level", callback_data="vocab_levels")],
        [InlineKeyboardButton("🔎 Search a Word", callback_data="vocab_search")],
        [InlineKeyboardButton("📝 Vocabulary Quiz", callback_data="vocab_quiz_levels")],
        [InlineKeyboardButton("🎯 Mixed-Level Quiz", callback_data="vocab_quiz:MIXED")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])
    await send_or_edit(update_or_query, text, markup)


def get_vocabulary(level=None, limit=1000):
    params = {"order": "id.asc"}
    if level and level != "MIXED":
        params["level"] = f"eq.{level}"
    return supabase_get("vocabulary", params=params, limit=limit)


def get_random_vocabulary(level=None):
    rows = get_vocabulary(level, 1000)
    return random.choice(rows) if rows else None


async def send_vocabulary(update_or_query, word, title="📖 Vocabulary"):
    if not word:
        await send_or_edit(
            update_or_query,
            "No vocabulary word was found. Please check your Supabase vocabulary table.",
            back_button("vocabulary"),
        )
        return

    word_id = word.get("id")
    text = (
        f"{title}\n\n"
        f"🔤 <b>{esc(word.get('word'), 'Unknown')}</b>\n"
        f"🎯 <b>Level:</b> {esc(word.get('level'), 'N/A')}\n"
        f"📌 <b>Meaning:</b> {esc(word.get('meaning'))}\n"
        f"💬 <b>Example:</b> {esc(word.get('example'))}"
    )

    category = clean(word.get("category"), "")
    synonyms = clean(word.get("synonyms"), "")
    antonyms = clean(word.get("antonyms"), "")

    if category:
        text += f"\n🏷️ <b>Category:</b> {esc(category)}"
    if synonyms:
        text += f"\n🔁 <b>Synonyms:</b> {esc(synonyms)}"
    if antonyms:
        text += f"\n↔️ <b>Antonyms:</b> {esc(antonyms)}"

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Another Word", callback_data="vocab_random")],
        [InlineKeyboardButton("📚 Choose Level", callback_data="vocab_levels")],
        [InlineKeyboardButton("🔎 Search", callback_data="vocab_search")],
        [InlineKeyboardButton("📝 Quiz", callback_data="vocab_quiz_levels")],
        [InlineKeyboardButton("🔙 Vocabulary", callback_data="vocabulary")],
    ])
    await send_or_edit(update_or_query, text, markup)


async def show_word_levels(update_or_query):
    await send_or_edit(
        update_or_query,
        "📚 <b>Choose Vocabulary Level</b>",
        level_keyboard("vocablevel"),
    )


async def show_quiz_levels(update_or_query):
    await send_or_edit(
        update_or_query,
        "📝 <b>Vocabulary Quiz</b>\n\nChoose a level:",
        level_keyboard("vocabquiz", include_mixed=True),
    )


async def start_vocab_quiz(update_or_query, context, level="MIXED"):
    rows = get_vocabulary(None if level == "MIXED" else level, 1000)
    if len(rows) < 4:
        await send_or_edit(
            update_or_query,
            f"Not enough vocabulary words are available for {esc(level_name(level))} quiz.",
            back_button("vocab_quiz_levels"),
        )
        return

    question_word = random.choice(rows)
    distractors = random.sample(
        [r for r in rows if r.get("id") != question_word.get("id")],
        3,
    )

    options = [question_word] + distractors
    random.shuffle(options)

    context.user_data["vocab_quiz"] = {
        "word_id": question_word.get("id"),
        "level": level,
    }

    buttons = []
    for row in options:
        # Only the database ID is stored in callback_data.
        buttons.append([
            InlineKeyboardButton(
                clean(row.get("meaning"), "Meaning unavailable")[:55],
                callback_data=f"vquizanswer:{row.get('id')}",
            )
        ])

    text = (
        "📝 <b>Vocabulary Quiz</b>\n\n"
        f"🎯 <b>{esc(level_name(level))}</b>\n\n"
        f"What is the meaning of:\n\n"
        f"🔤 <b>{esc(question_word.get('word'), 'Unknown')}</b>?"
    )
    await send_or_edit(update_or_query, text, InlineKeyboardMarkup(buttons))


async def check_vocab_answer(query, context, selected_id):
    state = context.user_data.get("vocab_quiz", {})
    correct_id = str(state.get("word_id", ""))

    try:
        rows = supabase_get(
            "vocabulary",
            params={"id": f"in.({correct_id},{selected_id})"},
            limit=5,
        )
    except Exception:
        rows = []

    selected = next((r for r in rows if str(r.get("id")) == str(selected_id)), None)
    correct = next((r for r in rows if str(r.get("id")) == correct_id), None)

    if not correct:
        await query.edit_message_text(
            "The quiz data could not be loaded. Please try again.",
            reply_markup=back_button("vocabulary"),
        )
        return

    is_correct = str(selected_id) == correct_id

    if is_correct:
        text = (
            "🎉 <b>Correct!</b>\n\n"
            f"🔤 <b>{esc(correct.get('word'))}</b>\n"
            f"📌 {esc(correct.get('meaning'))}\n\n"
            f"💬 {esc(correct.get('example'))}"
        )
    else:
        text = (
            "📚 <b>Let's learn from it!</b>\n\n"
            f"Your choice: {esc(selected.get('meaning') if selected else 'Unknown')}\n\n"
            f"Correct meaning of <b>{esc(correct.get('word'))}</b>:\n"
            f"📌 {esc(correct.get('meaning'))}\n\n"
            f"💬 {esc(correct.get('example'))}"
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next Question", callback_data=f"vocabquiz:{state.get('level', 'MIXED')}")],
            [InlineKeyboardButton("📖 Vocabulary", callback_data="vocabulary")],
        ]),
        parse_mode="HTML",
    )


async def ask_word_search(update_or_query, context):
    context.user_data["waiting_for_vocab_search"] = True
    await send_or_edit(
        update_or_query,
        "🔎 <b>Search a Word</b>\n\n"
        "Type an English word and I will search the Supabase vocabulary database.\n\n"
        "Example: <code>abundant</code>",
        back_button("vocabulary"),
    )


async def handle_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_vocab_search"):
        return False

    query_text = (update.message.text or "").strip()
    if not query_text:
        await update.message.reply_text("Please type a word.")
        return True

    context.user_data["waiting_for_vocab_search"] = False

    try:
        rows = supabase_get(
            "vocabulary",
            params={"word": f"ilike.*{query_text}*"},
            limit=10,
        )
    except Exception:
        rows = []

    if not rows:
        await update.message.reply_text(
            f"🔎 I couldn't find <b>{esc(query_text)}</b> in the vocabulary database.",
            reply_markup=back_button("vocabulary"),
            parse_mode="HTML",
        )
        return True

    buttons = []
    for row in rows:
        buttons.append([
            InlineKeyboardButton(
                f"{clean(row.get('word'), 'Word')} ({clean(row.get('level'), 'N/A')})",
                callback_data=f"vocabword:{row.get('id')}",
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Vocabulary", callback_data="vocabulary")])

    await update.message.reply_text(
        f"🔎 <b>Search results for:</b> {esc(query_text)}",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )
    return True


async def show_vocabulary_by_id(update_or_query, word_id):
    try:
        rows = supabase_get("vocabulary", params={"id": f"eq.{word_id}"}, limit=1)
        word = rows[0] if rows else None
    except Exception:
        word = None
    await send_vocabulary(update_or_query, word)


# ============================================================
# GRAMMAR
# ============================================================

async def show_grammar_levels(update_or_query):
    text = (
        "📝 <b>Grammar Practice</b>\n\n"
        "Choose your level. Grammar topics and questions are loaded from "
        "Supabase."
    )
    await send_or_edit(update_or_query, text, level_keyboard("grammarlevel"))


async def show_grammar_topics(update_or_query, level):
    try:
        topics = supabase_get(
            "grammar_topics",
            params={
                "level": f"eq.{level}",
                "published": "eq.true",
                "order": "sort_order.asc",
            },
            limit=50,
        )
    except Exception:
        topics = []

    buttons = []
    for topic in topics:
        buttons.append([
            InlineKeyboardButton(
                f"📝 {clean(topic.get('title'), 'Grammar topic')[:48]}",
                callback_data=f"gtopic:{topic.get('id')}",
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Levels", callback_data="grammar")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    text = f"📝 <b>Grammar · {esc(level)}</b>\n\nChoose a grammar topic:"
    if not topics:
        text += (
            "\n\nNo grammar topics have been added for this level yet. "
            "Add them to the Supabase <code>grammar_topics</code> table."
        )

    await send_or_edit(update_or_query, text, InlineKeyboardMarkup(buttons))


async def start_grammar_quiz(update_or_query, context, topic_id):
    try:
        topics = supabase_get("grammar_topics", params={"id": f"eq.{topic_id}"}, limit=1)
        questions = supabase_get(
            "grammar_questions",
            params={
                "topic_id": f"eq.{topic_id}",
                "published": "eq.true",
                "order": "sort_order.asc",
            },
            limit=50,
        )
    except Exception:
        topics, questions = [], []

    if not questions:
        await send_or_edit(
            update_or_query,
            "No grammar questions have been added for this topic yet.",
            back_button("grammar"),
        )
        return

    topic = topics[0] if topics else {}
    context.user_data["grammar_quiz"] = {
        "topic_id": topic_id,
        "questions": questions,
        "index": 0,
        "score": 0,
    }

    await send_grammar_question(update_or_query, context)


async def send_grammar_question(update_or_query, context):
    state = context.user_data.get("grammar_quiz")
    if not state:
        await send_or_edit(update_or_query, "Grammar session ended.", back_button("grammar"))
        return

    questions = state["questions"]
    index = state["index"]

    if index >= len(questions):
        score = state["score"]
        total = len(questions)
        await send_or_edit(
            update_or_query,
            f"🏆 <b>Grammar Result</b>\n\n"
            f"You scored <b>{score}/{total}</b>.\n\n"
            "Keep practising and try the topic again!",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"gtopic:{state['topic_id']}")],
                [InlineKeyboardButton("📝 Grammar", callback_data="grammar")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
        )
        return

    q = questions[index]
    options = [
        ("A", q.get("option_a")),
        ("B", q.get("option_b")),
        ("C", q.get("option_c")),
        ("D", q.get("option_d")),
    ]

    buttons = [
        [InlineKeyboardButton(
            f"{letter}. {clean(value, 'Option')[:52]}",
            callback_data=f"ganswer:{index}:{letter}",
        )]
        for letter, value in options
    ]

    text = (
        f"📝 <b>Grammar Question {index + 1}/{len(questions)}</b>\n\n"
        f"{esc(q.get('question'), 'Question unavailable')}"
    )
    await send_or_edit(update_or_query, text, InlineKeyboardMarkup(buttons))


async def check_grammar_answer(query, context, index, selected):
    state = context.user_data.get("grammar_quiz")
    if not state:
        await query.edit_message_text("This grammar session has expired.", reply_markup=back_button("grammar"))
        return

    questions = state["questions"]
    if index >= len(questions):
        await send_grammar_question(query, context)
        return

    q = questions[index]
    correct = clean(q.get("correct_option"), "").upper()
    selected = selected.upper()

    if selected == correct:
        state["score"] += 1
        result = "✅ <b>Correct!</b>"
    else:
        result = f"❌ <b>Not quite.</b>\nThe correct answer is <b>{esc(correct)}</b>."

    explanation = clean(q.get("explanation"), "")
    text = result
    if explanation:
        text += f"\n\n💡 {esc(explanation)}"

    state["index"] += 1

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next Question", callback_data="gnext")],
        ]),
        parse_mode="HTML",
    )


# ============================================================
# SPEAKING
# ============================================================

async def show_speaking(update_or_query):
    text = (
        "🗣️ <b>Speaking Practice</b>\n\n"
        "Choose a level for conversation practice."
    )
    await send_or_edit(update_or_query, text, level_keyboard("speakinglevel"))


async def show_speaking_categories(update_or_query, level):
    try:
        rows = supabase_get(
            "speaking_topics",
            params={
                "level": f"eq.{level}",
                "published": "eq.true",
                "order": "sort_order.asc",
            },
            limit=100,
        )
    except Exception:
        rows = []

    categories = []
    for row in rows:
        category = clean(row.get("category"), "Everyday Conversations")
        if category not in categories:
            categories.append(category)

    buttons = [
        [InlineKeyboardButton(
            f"💬 {category[:45]}",
            callback_data=f"scategory:{level}:{i}",
        )]
        for i, category in enumerate(categories)
    ]
    # Store categories for this chat so callback IDs stay short.
    context_data = getattr(update_or_query, "_context_data", None)
    buttons.append([InlineKeyboardButton("🔙 Levels", callback_data="speaking")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    # Categories are easier to select directly from the database in the next screen.
    # We encode a safe category slug using the topic IDs below instead.
    buttons = []
    for row in rows:
        buttons.append([
            InlineKeyboardButton(
                f"💬 {clean(row.get('title'), 'Speaking topic')[:48]}",
                callback_data=f"stopic:{row.get('id')}",
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Levels", callback_data="speaking")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    text = f"🗣️ <b>Speaking · {esc(level)}</b>\n\nChoose a speaking topic:"
    if not rows:
        text += (
            "\n\nNo speaking topics have been added for this level yet. "
            "Add them to the Supabase <code>speaking_topics</code> table."
        )

    await send_or_edit(update_or_query, text, InlineKeyboardMarkup(buttons))


async def show_speaking_topic(update_or_query, topic_id):
    try:
        topics = supabase_get("speaking_topics", params={"id": f"eq.{topic_id}"}, limit=1)
        questions = supabase_get(
            "speaking_questions",
            params={
                "topic_id": f"eq.{topic_id}",
                "published": "eq.true",
                "order": "sort_order.asc",
            },
            limit=50,
        )
        roleplays = supabase_get(
            "roleplays",
            params={
                "topic_id": f"eq.{topic_id}",
                "published": "eq.true",
                "order": "sort_order.asc",
            },
            limit=50,
        )
    except Exception:
        topics, questions, roleplays = [], [], []

    topic = topics[0] if topics else None
    if not topic:
        await send_or_edit(update_or_query, "Speaking topic not found.", back_button("speaking"))
        return

    text = (
        f"🗣️ <b>{esc(topic.get('title'), 'Speaking Topic')}</b>\n\n"
        f"{esc(topic.get('description'), 'Practise this topic aloud.')}\n\n"
        "Choose a practice mode:"
    )

    buttons = []
    if questions:
        buttons.append([InlineKeyboardButton(
            "❓ Questions & Answers",
            callback_data=f"squestions:{topic_id}",
        )])
    if roleplays:
        buttons.append([InlineKeyboardButton(
            "🎭 Role-play Practice",
            callback_data=f"roleplay:{topic_id}:0",
        )])

    buttons.extend([
        [InlineKeyboardButton("🔙 Speaking Topics", callback_data=f"slevel:{topic.get('level', 'A1')}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])

    await send_or_edit(update_or_query, text, InlineKeyboardMarkup(buttons))


async def show_speaking_questions(update_or_query, context, topic_id):
    try:
        questions = supabase_get(
            "speaking_questions",
            params={
                "topic_id": f"eq.{topic_id}",
                "published": "eq.true",
                "order": "sort_order.asc",
            },
            limit=50,
        )
    except Exception:
        questions = []

    if not questions:
        await send_or_edit(update_or_query, "No speaking questions are available.", back_button("speaking"))
        return

    context.user_data["speaking_questions"] = {
        "topic_id": topic_id,
        "questions": questions,
        "index": 0,
    }
    await send_speaking_question(update_or_query, context)


async def send_speaking_question(update_or_query, context):
    state = context.user_data.get("speaking_questions")
    if not state:
        await send_or_edit(update_or_query, "Speaking session ended.", back_button("speaking"))
        return

    questions = state["questions"]
    index = state["index"]

    if index >= len(questions):
        await send_or_edit(
            update_or_query,
            "🎉 <b>Speaking practice complete!</b>\n\n"
            "Try answering the questions again without looking at the model answers.",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🗣️ Speaking", callback_data="speaking")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
        )
        return

    q = questions[index]
    text = (
        f"🗣️ <b>Speaking Question {index + 1}/{len(questions)}</b>\n\n"
        f"❓ {esc(q.get('question'), 'Question unavailable')}\n\n"
        "💡 <b>Model Answer</b>\n"
        f"{esc(q.get('model_answer'), 'Try answering in your own words.')}"
    )

    await send_or_edit(
        update_or_query,
        text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next Question", callback_data="snext")],
            [InlineKeyboardButton("🔙 Topic", callback_data=f"stopic:{state['topic_id']}")],
        ]),
    )


async def show_roleplay(update_or_query, context, topic_id, index=0):
    try:
        rows = supabase_get(
            "roleplays",
            params={
                "topic_id": f"eq.{topic_id}",
                "published": "eq.true",
                "order": "sort_order.asc",
            },
            limit=50,
        )
    except Exception:
        rows = []

    if not rows:
        await send_or_edit(update_or_query, "No role-play practice is available.", back_button("speaking"))
        return

    index = int(index)
    if index >= len(rows):
        await send_or_edit(
            update_or_query,
            "🎭 <b>Role-play complete!</b>\n\n"
            "Try the situation again and change your answers naturally.",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🗣️ Speaking", callback_data="speaking")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
        )
        return

    role = rows[index]
    text = (
        f"🎭 <b>Role-play {index + 1}/{len(rows)}</b>\n\n"
        f"<b>Situation:</b> {esc(role.get('situation'))}\n\n"
        f"👤 <b>Your Role:</b> {esc(role.get('your_role'))}\n"
        f"🧑 <b>Partner:</b> {esc(role.get('partner_role'))}\n\n"
        f"💬 <b>Partner says:</b>\n{esc(role.get('partner_line'))}\n\n"
        f"🗣️ <b>Your task:</b>\n{esc(role.get('your_task'))}"
    )

    buttons = []
    if index + 1 < len(rows):
        buttons.append([InlineKeyboardButton("➡️ Next Role-play", callback_data=f"roleplay:{topic_id}:{index + 1}")])
    buttons.extend([
        [InlineKeyboardButton("🔙 Topic", callback_data=f"stopic:{topic_id}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])
    await send_or_edit(update_or_query, text, InlineKeyboardMarkup(buttons))


# ============================================================
# ABOUT
# ============================================================

async def show_about(update_or_query):
    text = (
        "ℹ️ <b>The Speaking English Channel</b>\n\n"
        "Learn English with real-life conversations, vocabulary, grammar, "
        "podcasts and speaking practice.\n\n"
        "📚 Lessons: A1–C2\n"
        "📖 Vocabulary: A1–C2\n"
        "📝 Grammar: A1–C2\n"
        "🗣️ Speaking: conversations, questions and role-plays\n\n"
        "🌐 All learning content is managed through Supabase."
    )
    await send_or_edit(
        update_or_query,
        text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 YouTube Channel", url=YOUTUBE_URL)],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]),
    )


# ============================================================
# CALLBACK ROUTER
# ============================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    try:
        if data == "main_menu":
            context.user_data.clear()
            await query.edit_message_text(WELCOME, reply_markup=main_menu(), parse_mode="HTML")

        elif data == "learn":
            await show_learn(query)

        elif data.startswith("lesson:"):
            await show_level_lessons(query, data.split(":", 1)[1])

        elif data.startswith("lessonview:"):
            await show_lesson(query, data.split(":", 1)[1])

        elif data == "podcasts":
            await show_podcasts(query)

        elif data == "videos":
            await show_videos(query)

        elif data == "vocabulary":
            await show_vocabulary_menu(query)

        elif data == "vocab_random":
            await send_vocabulary(query, get_random_vocabulary(), "🎲 Random Vocabulary")

        elif data == "vocab_levels":
            await show_word_levels(query)

        elif data.startswith("vocablevel:"):
            await send_vocabulary(
                query,
                get_random_vocabulary(data.split(":", 1)[1]),
                f"📚 {data.split(':', 1)[1]} Vocabulary",
            )

        elif data == "vocab_search":
            await ask_word_search(query, context)

        elif data == "vocab_quiz_levels":
            await show_quiz_levels(query)

        elif data.startswith("vocabquiz:"):
            await start_vocab_quiz(query, context, data.split(":", 1)[1])

        elif data.startswith("vquizanswer:"):
            await check_vocab_answer(query, context, data.split(":", 1)[1])

        elif data.startswith("vocabword:"):
            await show_vocabulary_by_id(query, data.split(":", 1)[1])

        elif data == "grammar":
            await show_grammar_levels(query)

        elif data.startswith("grammarlevel:"):
            await show_grammar_topics(query, data.split(":", 1)[1])

        elif data.startswith("gtopic:"):
            await start_grammar_quiz(query, context, data.split(":", 1)[1])

        elif data.startswith("ganswer:"):
            _, index, selected = data.split(":")
            await check_grammar_answer(query, context, int(index), selected)

        elif data == "gnext":
            await send_grammar_question(query, context)

        elif data == "speaking":
            await show_speaking(query)

        elif data.startswith("slevel:"):
            await show_speaking_categories(query, data.split(":", 1)[1])

        elif data.startswith("stopic:"):
            await show_speaking_topic(query, data.split(":", 1)[1])

        elif data.startswith("squestions:"):
            await show_speaking_questions(query, context, data.split(":", 1)[1])

        elif data == "snext":
            state = context.user_data.get("speaking_questions")
            if state:
                state["index"] += 1
                await send_speaking_question(query, context)
            else:
                await show_speaking(query)

        elif data.startswith("roleplay:"):
            _, topic_id, index = data.split(":")
            await show_roleplay(query, context, topic_id, int(index))

        elif data == "about":
            await show_about(query)

    except Exception as exc:
        print("Callback error:", repr(exc))
        try:
            await query.edit_message_text(
                "Something went wrong. Please try again.",
                reply_markup=main_menu(),
            )
        except Exception:
            pass


# ============================================================
# COMMANDS
# ============================================================

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_learn(update)


async def podcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_podcasts(update)


async def youtube_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_videos(update)


async def vocabulary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_vocabulary_menu(update)


async def grammar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_grammar_levels(update)


async def speaking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_speaking(update)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_about(update)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    handled = await handle_text_search(update, context)
    if handled:
        return


# ============================================================
# RUN
# ============================================================

def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("podcast", podcast_command))
    application.add_handler(CommandHandler("videos", youtube_command))
    application.add_handler(CommandHandler("vocabulary", vocabulary_command))
    application.add_handler(CommandHandler("grammar", grammar_command))
    application.add_handler(CommandHandler("speaking", speaking_command))
    application.add_handler(CommandHandler("about", about_command))

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("The Speaking English Channel Bot is running.")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
