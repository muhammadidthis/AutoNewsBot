from __future__ import annotations

from typing import Iterable

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from .config import DEFAULT_TOPICS, ARTICLES_PER_TOPIC
from .news import TOPIC_TO_FEEDS, get_latest_articles_for_topic
from .storage import get_user_topics, set_user_topics, get_user_settings, update_user_settings
from .summarize import summarize_text


def _topic_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for topic in TOPIC_TO_FEEDS.keys():
        is_on = topic in selected
        label = ("✅ " if is_on else "⬜ ") + topic.capitalize()
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"toggle:{topic}")])
    buttons.append([InlineKeyboardButton(text="Done ✅", callback_data="done")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    topics = get_user_topics(user_id, DEFAULT_TOPICS)
    settings = get_user_settings(user_id, DEFAULT_TOPICS)
    await update.message.reply_text(
        "Welcome! Choose your topics to get summarized news. You can change these anytime with /topics.\n"
        "Use /help to see all commands.",
        reply_markup=_topic_keyboard(topics),
    )


async def topics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    topics = get_user_topics(user_id, DEFAULT_TOPICS)
    await update.message.reply_text("Select topics:", reply_markup=_topic_keyboard(topics))


async def toggle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data == "done":
        await query.edit_message_text("Topics saved. Use /latest to get news.")
        return
    if not data.startswith("toggle:"):
        return
    topic = data.split(":", 1)[1]
    current = get_user_topics(user_id, DEFAULT_TOPICS)
    if topic in current:
        current = [t for t in current if t != topic]
    else:
        current = list(dict.fromkeys(current + [topic]))
    set_user_topics(user_id, current)
    await query.edit_message_reply_markup(reply_markup=_topic_keyboard(current))


def _format_article(title: str, url: str, summary: str) -> str:
    # Keep it short for Telegram
    if len(summary) > 600:
        summary = summary[:600].rstrip() + "…"
    return f"<b>{title}</b>\n{summary}\n<a href=\"{url}\">Read more</a>"


async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    topics = get_user_topics(user_id, DEFAULT_TOPICS)
    settings = get_user_settings(user_id, DEFAULT_TOPICS)
    if not topics:
        await update.message.reply_text("No topics selected. Use /topics to choose.")
        return
    await update.message.reply_text("Fetching and summarizing articles… This may take a few seconds.")

    messages: list[str] = []
    for topic in topics:
        per_topic = int(settings.get("latest_count", ARTICLES_PER_TOPIC))
        articles = get_latest_articles_for_topic(topic, limit=per_topic)
        if not articles:
            continue
        section_lines = [f"<u><b>{topic.capitalize()}</b></u>"]
        for art in articles:
            summary = summarize_text(art.content or art.summary or "", max_sentences=3)
            section_lines.append(_format_article(art.title, art.url, summary))
        messages.append("\n\n".join(section_lines))

    if not messages:
        await update.message.reply_text("No recent articles found right now. Please try later.")
        return

    # Send as multiple messages if too long
    for part in messages:
        await update.message.reply_text(part, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "/start - Begin and choose your topics\n"
        "/topics - Update your topic preferences\n"
        "/latest - Get summarized news now\n"
        "/setlatestcount <n> - Articles per topic for /latest\n"
        "/setdailycount <n> - Articles per topic in daily digest\n"
        "/schedule <morning|evening|night> - Set daily digest time\n"
        "/subscribe - Receive daily digest automatically\n"
        "/unsubscribe - Stop daily digest\n"
        "/help - Show this help"
    )
    await update.message.reply_text(text)


async def set_latest_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /setlatestcount <number>")
        return
    try:
        n = max(1, min(10, int(context.args[0])))
    except ValueError:
        await update.message.reply_text("Please provide a number between 1 and 10.")
        return
    update_user_settings(user_id, latest_count=n)
    await update.message.reply_text(f"Set articles per topic for /latest to {n}.")


async def set_daily_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /setdailycount <number>")
        return
    try:
        n = max(1, min(10, int(context.args[0])))
    except ValueError:
        await update.message.reply_text("Please provide a number between 1 and 10.")
        return
    update_user_settings(user_id, daily_count=n)
    await update.message.reply_text(f"Set articles per topic in daily digest to {n}.")


def _schedule_to_hour(schedule: str) -> int:
    schedule = (schedule or "morning").lower()
    if schedule == "evening":
        return 18
    if schedule == "night":
        return 22
    return 8


async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    if not context.args or context.args[0].lower() not in {"morning", "evening", "night"}:
        await update.message.reply_text("Usage: /schedule <morning|evening|night>")
        return
    slot = context.args[0].lower()
    update_user_settings(user_id, schedule=slot)
    await update.message.reply_text(f"Daily digest time set to {slot}.")


async def _send_daily_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    user_id = int(job.chat_id)
    # Build a fake Update-less send using bot directly
    from .config import DEFAULT_TOPICS
    topics = get_user_topics(user_id, DEFAULT_TOPICS)
    settings = get_user_settings(user_id, DEFAULT_TOPICS)
    if not topics:
        return
    per_topic = int(settings.get("daily_count", 5))
    messages: list[str] = []
    for topic in topics:
        articles = get_latest_articles_for_topic(topic, limit=per_topic)
        if not articles:
            continue
        section_lines = [f"<u><b>{topic.capitalize()}</b></u>"]
        for art in articles:
            summary = summarize_text(art.content or art.summary or "", max_sentences=3)
            section_lines.append(_format_article(art.title, art.url, summary))
        messages.append("\n\n".join(section_lines))
    if not messages:
        return
    for part in messages:
        await context.bot.send_message(chat_id=user_id, text=part, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def _schedule_user_job(app: Application, user_id: int, schedule: str) -> None:
    # Remove existing job for user
    if app.job_queue is None:
        return
    job_name = f"digest:{user_id}"
    for job in app.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    # Add new daily job at the selected hour (local time)
    hour = _schedule_to_hour(schedule)
    from datetime import time as dtime
    from tzlocal import get_localzone
    tz = get_localzone()
    app.job_queue.run_daily(_send_daily_digest, time=dtime(hour=hour, minute=0, tzinfo=tz), name=job_name, chat_id=user_id)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    settings = get_user_settings(user_id, DEFAULT_TOPICS)
    if settings.get("subscribed"):
        await update.message.reply_text("You are already subscribed to daily digests.")
        return
    settings = update_user_settings(user_id, subscribed=True)
    _schedule_user_job(context.application, user_id, settings.get("schedule", "morning"))
    await update.message.reply_text("Subscribed. You will receive a daily digest at your scheduled time.")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    user_id = update.effective_user.id
    settings = get_user_settings(user_id, DEFAULT_TOPICS)
    if not settings.get("subscribed"):
        await update.message.reply_text("You are not subscribed.")
        return
    update_user_settings(user_id, subscribed=False)
    if context.application.job_queue is not None:
        job_name = f"digest:{user_id}"
        for job in context.application.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
    await update.message.reply_text("Unsubscribed from daily digests.")


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("topics", topics))
    app.add_handler(CallbackQueryHandler(toggle_topic))
    app.add_handler(CommandHandler("latest", latest))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setlatestcount", set_latest_count))
    app.add_handler(CommandHandler("setdailycount", set_daily_count))
    app.add_handler(CommandHandler("schedule", schedule_cmd))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    return app

