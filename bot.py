"""
bot.py
------
Main Telegram bot: handlers, /panel UI, timer job, message listener, /getlogs.
"""

import asyncio
import json
import os
from functools import partial
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, File
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import (
    TELEGRAM_TOKEN,
    PRESET_TOPICS,
    DEBATE_MODES,
    MODELS,
    DEFAULT_MODEL,
    TIMER_PRESETS,
    MESSAGE_LIMIT_OPTIONS,
    PRIVACY_MODE_GUIDE,
    logger,
)
from debate import DebateManager, generate_timer_bar
import gemini

# Global state
debate_manager = DebateManager()
panel_state = {}  # chat_id -> {mode, timer, message_limit, model, topic}


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome + Privacy Mode guide."""
    msg = f"""🎙️ **Tech Debate Bot**

Start debates, configure rules, and let Gemini AI judge the winner!

**Commands:**
/panel - Configure and start a debate
/getlogs - Download activity logs
/cancel - Stop active debate

{PRIVACY_MODE_GUIDE}"""
    
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    logger.info(f"User {update.effective_user.id} started bot")


async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Interactive control panel for debate configuration."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if debate_manager.has_session(chat_id):
        await update.message.reply_text("❌ Debate already active! Use /cancel first.")
        return

    # Initialize panel state for this chat
    panel_state[chat_id] = {
        "mode": None,
        "timer": None,
        "message_limit": None,
        "model": DEFAULT_MODEL,
        "topic": None,
        "user_id": user_id,
    }

    # Render initial /panel UI
    await show_panel_ui(chat_id, context)


async def show_panel_ui(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Render the /panel control panel."""
    state = panel_state.get(chat_id, {})

    mode_str = state.get("mode") or "❌ Not set"
    timer_str = state.get("timer") or "❌ Not set"
    limit_str = state.get("message_limit") or "❌ Not set"
    model_str = state.get("model") or DEFAULT_MODEL
    topic_str = state.get("topic") or "❌ Not set"

    keyboard = [
        # Mode selection
        [
            InlineKeyboardButton("Human vs AI", callback_data="mode_human_vs_ai"),
            InlineKeyboardButton("1v1 Silent", callback_data="mode_1v1_silent"),
            InlineKeyboardButton("1v1 Sportscaster", callback_data="mode_1v1_sportscaster"),
        ],
        # Timer selection
        [
            InlineKeyboardButton("30s", callback_data="timer_30"),
            InlineKeyboardButton("60s", callback_data="timer_60"),
            InlineKeyboardButton("120s", callback_data="timer_120"),
            InlineKeyboardButton("240s", callback_data="timer_240"),
            InlineKeyboardButton("300s", callback_data="timer_300"),
        ],
        # Message limit
        [
            InlineKeyboardButton("1 per person", callback_data="limit_1"),
            InlineKeyboardButton("2 per person", callback_data="limit_2"),
            InlineKeyboardButton("Unlimited", callback_data="limit_999"),
        ],
        # Model selector
        [
            InlineKeyboardButton("⚡ Lite", callback_data="model_lite"),
            InlineKeyboardButton("⚙️ Flash", callback_data="model_flash"),
            InlineKeyboardButton("🧠 Pro", callback_data="model_pro"),
        ],
        # Topic selector
        [
            InlineKeyboardButton("Topics", callback_data="topic_menu"),
        ],
        # START button (only if all fields set)
        [
            InlineKeyboardButton(
                "🚀 START DEBATE" if all([
                    state.get("mode"),
                    state.get("timer"),
                    state.get("message_limit"),
                    state.get("topic"),
                ]) else "⏳ Set all options first",
                callback_data="start_debate" if all([
                    state.get("mode"),
                    state.get("timer"),
                    state.get("message_limit"),
                    state.get("topic"),
                ]) else "noop",
            ),
        ],
    ]

    text = f"""⚙️ **DEBATE CONFIGURATION**

**Mode:** {mode_str}
**Timer:** {timer_str}
**Messages per person:** {limit_str}
**Model:** {model_str}
**Topic:** {topic_str}

Click buttons to configure, then START."""

    try:
        await asyncio.get_running_loop().run_in_executor(
            None,
            partial(
                context.bot.send_message,
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard),
            ),
        )
    except Exception as e:
        logger.error(f"Failed to show panel UI: {e}")


async def topic_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show preset topic selection."""
    chat_id = update.effective_chat.id
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(topic, callback_data=f"topic_{i}")]
        for i, topic in enumerate(PRESET_TOPICS)
    ]
    keyboard.append([InlineKeyboardButton("Custom Topic", callback_data="topic_custom")])

    await query.edit_message_text(
        "📚 **SELECT TOPIC**\n\nClick a preset or choose Custom:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )


async def topic_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle preset topic selection."""
    chat_id = update.effective_chat.id
    query = update.callback_query
    await query.answer()

    topic_idx = int(query.data.split("_")[1])
    topic = PRESET_TOPICS[topic_idx]
    panel_state[chat_id]["topic"] = topic

    await query.edit_message_text(f"✅ Topic: {topic}")
    await asyncio.sleep(1)
    await show_panel_ui(chat_id, context)


async def topic_custom_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for custom topic input."""
    chat_id = update.effective_chat.id
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📝 Reply with your custom topic:\n\n/topic My Custom Topic"
    )
    context.user_data[f"{chat_id}_awaiting_topic"] = True


async def topic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /topic <custom topic> command."""
    chat_id = update.effective_chat.id
    custom_topic = " ".join(context.args) if context.args else None

    if not custom_topic:
        await update.message.reply_text("Usage: /topic My Custom Topic Name")
        return

    panel_state[chat_id]["topic"] = f"🎯 Custom: {custom_topic}"
    await update.message.reply_text(f"✅ Custom topic set: {custom_topic}")
    logger.info(f"Custom topic set | chat={chat_id} | topic={custom_topic}")

    await show_panel_ui(chat_id, context)


# Generic callback for mode/timer/limit/model buttons
async def panel_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all /panel configuration button clicks."""
    chat_id = update.effective_chat.id
    query = update.callback_query
    data = query.data
    await query.answer()

    if not data.startswith(("mode_", "timer_", "limit_", "model_")):
        return

    # Parse button data
    if data.startswith("mode_"):
        mode = data.split("_", 1)[1]
        panel_state[chat_id]["mode"] = mode
        logger.info(f"Mode selected | chat={chat_id} | mode={mode}")

    elif data.startswith("timer_"):
        timer_sec = int(data.split("_")[1])
        panel_state[chat_id]["timer"] = timer_sec
        logger.info(f"Timer selected | chat={chat_id} | timer={timer_sec}s")

    elif data.startswith("limit_"):
        limit = int(data.split("_")[1])
        panel_state[chat_id]["message_limit"] = limit
        logger.info(f"Limit selected | chat={chat_id} | limit={limit}")

    elif data.startswith("model_"):
        model_key = data.split("_")[1]
        model_map = {
            "lite": "gemini-2.5-flash-lite",
            "flash": "gemini-2.5-flash",
            "pro": "gemini-1.5-pro",
        }
        panel_state[chat_id]["model"] = model_map.get(model_key, DEFAULT_MODEL)
        logger.info(f"Model selected | chat={chat_id} | model={panel_state[chat_id]['model']}")

    # Refresh panel UI
    await show_panel_ui(chat_id, context)


async def start_debate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """START DEBATE button - launch the debate with current config."""
    chat_id = update.effective_chat.id
    query = update.callback_query

    if query.data != "start_debate":
        await query.answer()
        return

    state = panel_state.get(chat_id, {})
    if not all([state.get("mode"), state.get("timer"), state.get("message_limit"), state.get("topic")]):
        await query.answer("❌ Please set all options first.", show_alert=True)
        return

    await query.answer()

    # Create debate session
    try:
        session = debate_manager.create_session(
            chat_id=chat_id,
            topic=state["topic"],
            mode=state["mode"],
            timer_seconds=state["timer"],
            message_limit=state["message_limit"],
            model=state["model"],
        )

        msg = (
            f"🏆 **DEBATE STARTED**\n\n"
            f"**Topic:** {session.topic}\n"
            f"**Mode:** {DEBATE_MODES.get(session.mode, session.mode)}\n"
            f"**Timer:** {session.timer_seconds}s | **Messages:** {session.message_limit}\n"
            f"**Model:** {session.model}\n\n"
            f"💬 Send your arguments now!"
        )

        msg_obj = await context.bot.send_message(
            chat_id, msg, parse_mode=ParseMode.MARKDOWN
        )
        session.status_message_id = msg_obj.message_id

        # Start live timer job
        await start_timer_job(chat_id, context)

        # Clean up panel state
        if chat_id in panel_state:
            del panel_state[chat_id]

        logger.info(f"Debate started | {session.chat_id}")

    except Exception as e:
        logger.error(f"Failed to start debate: {e}")
        await context.bot.send_message(chat_id, f"❌ Error starting debate: {e}")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Safe cancel (use .pop() to avoid KeyError)."""
    chat_id = update.effective_chat.id
    session = debate_manager.end_session(chat_id)

    if session:
        await update.message.reply_text("⏹️ Debate cancelled.")
        logger.info(f"Debate cancelled | chat={chat_id}")
    else:
        await update.message.reply_text("❌ No active debate to cancel.")


async def getlogs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upload bot_activity.log as a file."""
    user_id = update.effective_user.id

    if not os.path.exists("bot_activity.log"):
        await update.message.reply_text("❌ No log file found yet.")
        return

    try:
        with open("bot_activity.log", "rb") as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename="bot_activity.log",
            )
        logger.info(f"Logs downloaded | user={user_id}")
    except Exception as e:
        logger.error(f"Failed to send logs: {e}")
        await update.message.reply_text(f"❌ Error sending logs: {e}")


# ============================================================================
# MESSAGE LISTENER & DEBATE FLOW
# ============================================================================

async def message_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text/photo/video messages during active debates."""
    chat_id = update.effective_chat.id
    message = update.message
    user = update.effective_user

    session = debate_manager.get_session(chat_id)
    if not session:
        return  # No active debate

    # Extract text or media
    text = message.text or message.caption or ""
    media_type = None
    media_bytes = {}

    if message.photo:
        media_type = "photo"
        try:
            file_obj = await message.photo[-1].get_file()
            data = await file_obj.download_as_bytearray()
            media_bytes["image/jpeg"] = bytes(data)
            logger.info(f"Photo downloaded | user={user.id} | size={len(data)}")
        except Exception as e:
            logger.error(f"Failed to download photo: {e}")
            await message.reply_text("❌ Couldn't download your photo.")
            return

    elif message.video:
        media_type = "video"
        try:
            file_obj = await message.video.get_file()
            data = await file_obj.download_as_bytearray()
            media_bytes["video/mp4"] = bytes(data)
            logger.info(f"Video downloaded | user={user.id} | size={len(data)}")
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            await message.reply_text("❌ Couldn't download your video.")
            return

    if not text and not media_bytes:
        return  # Empty message

    # Check message limit
    if not session.can_user_submit(user.id):
        limit = session.message_limit
        await message.reply_text(
            f"❌ You've reached your {limit}-message limit for this debate."
        )
        return

    session.increment_user_message(user.id)
    session.add_submission(user.id, user.full_name or user.username or f"User{user.id}", text, media_type)

    # React based on debate mode
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

    try:
        if session.mode == "human_vs_ai":
            # Generate counter-argument
            response = await gemini.counter_argument(
                text, media_bytes, session
            )
            await context.bot.send_message(
                chat_id,
                f"⚔️ **AI Counter:**\n{response}",
                parse_mode=ParseMode.MARKDOWN,
            )

        elif session.mode == "1v1_sportscaster":
            # Generate live commentary
            transcript = session.get_transcript()
            response = await gemini.sportscaster_comment(transcript, session)
            await context.bot.send_message(
                chat_id,
                f"🎙️ **Commentator:** {response}",
                parse_mode=ParseMode.MARKDOWN,
            )

        # 1v1_silent mode: don't call Gemini, just log
        logger.info(f"Message processed | chat={chat_id} | mode={session.mode}")

    except gemini.GeminiError as e:
        logger.error(f"Gemini error: {e}")
        await context.bot.send_message(chat_id, f"⚠️ {e}")


# ============================================================================
# TIMER JOB
# ============================================================================

async def start_timer_job(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Start background timer that updates status message every 5s."""
    try:
        # Create async task for timer
        task = asyncio.create_task(timer_tick_job(chat_id, context))
        session = debate_manager.get_session(chat_id)
        if session:
            session.timer_job_id = id(task)
        logger.info(f"Timer job started | chat={chat_id}")
    except Exception as e:
        logger.error(f"Failed to start timer job: {e}")


async def timer_tick_job(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Update timer bar every 5 seconds, end debate when time runs out."""
    while True:
        try:
            await asyncio.sleep(5)
            session = debate_manager.get_session(chat_id)
            if not session:
                break  # Debate ended

            remaining = session.seconds_remaining()
            bar = generate_timer_bar(remaining, session.timer_seconds)

            # Update status message
            if session.status_message_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=session.status_message_id,
                        text=f"⏱️ {bar}\n\n💬 Arguments: {len(session.submissions)}",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass  # Message may not exist anymore

            # Check if time expired
            if remaining <= 0:
                logger.info(f"Timer expired | chat={chat_id}")
                await end_debate(chat_id, context)
                break

        except asyncio.CancelledError:
            logger.info(f"Timer job cancelled | chat={chat_id}")
            break
        except Exception as e:
            logger.error(f"Timer job error: {e}")
            break


async def end_debate(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """End debate, generate verdict, clean up."""
    session = debate_manager.get_session(chat_id)
    if not session:
        return

    await context.bot.send_message(chat_id, "⏳ Time's up! Generating verdict...")

    try:
        verdict = await gemini.final_verdict(session)
        await context.bot.send_message(
            chat_id,
            f"📊 **FINAL VERDICT**\n\n{verdict}",
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info(f"Debate verdict generated | chat={chat_id}")
    except gemini.GeminiError as e:
        logger.error(f"Verdict generation failed: {e}")
        await context.bot.send_message(chat_id, f"❌ Verdict generation failed: {e}")

    debate_manager.end_session(chat_id)


# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                update.effective_chat.id,
                "⚠️ An unexpected error occurred. Try /panel to restart.",
            )
        except Exception:
            pass


# ============================================================================
# APPLICATION SETUP
# ============================================================================

def build_app() -> Application:
    """Build and configure the Telegram bot application."""
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("panel", panel_command))
    app.add_handler(CommandHandler("topic", topic_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("getlogs", getlogs_command))

    # Callback handlers (inline keyboard buttons)
    app.add_handler(CallbackQueryHandler(topic_menu_callback, pattern="^topic_menu$"))
    app.add_handler(CallbackQueryHandler(topic_preset_callback, pattern="^topic_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(topic_custom_callback, pattern="^topic_custom$"))
    app.add_handler(CallbackQueryHandler(panel_button_callback, pattern="^(mode_|timer_|limit_|model_)"))
    app.add_handler(CallbackQueryHandler(start_debate_callback, pattern="^start_debate$"))

    # Message listener (text, photo, video)
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND,
            message_listener,
        )
    )

    # Error handler
    app.add_error_handler(error_handler)

    return app


def main():
    """Entry point."""
    logger.info("🚀 Starting Tech Debate Bot...")
    app = build_app()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
