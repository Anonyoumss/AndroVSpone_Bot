"""
config.py
---------
Central configuration: env vars, preset topics, models, system prompts, logging.
"""

import os
import logging
import logging.handlers
from dotenv import load_dotenv

load_dotenv()

# --- Secrets ---------------------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise RuntimeError(
        "Missing TELEGRAM_TOKEN or GEMINI_API_KEY in .env\n"
        "Create .env with:\nTELEGRAM_TOKEN=...\nGEMINI_API_KEY=..."
    )

# --- Preset Topics (7 + custom fallback) -----------------------------------
PRESET_TOPICS = [
    "🤖 Android vs. iOS: Customization vs. Ecosystem",
    "🎨 Nothing OS vs. Pixel UI: Minimalist Design War",
    "⚡ Apple M-Series vs. Snapdragon X Elite: Efficiency",
    "🏗️ Custom Hardware vs. Out-of-the-Box Flagships",
    "📱 Native Apps vs. Cross-Platform Web Apps",
    "🧠 Local On-Device AI vs. Cloud AI Infrastructure",
    "📺 120Hz LTPO OLED vs. Battery Longevity Trade-offs",
]

# --- Debate Modes ----------------------------------------------------------
DEBATE_MODES = {
    "human_vs_ai": "Human vs AI (AI replies live)",
    "1v1_silent": "1v1 Humans (AI judges only at end)",
    "1v1_sportscaster": "1v1 Humans (AI commentates live)",
}

# --- Models ----------------------------------------------------------------
MODELS = {
    "gemini-2.5-flash-lite": "⚡ Ultra-fast (lite)",
    "gemini-2.5-flash": "⚙️ Balanced (standard)",
    "gemini-1.5-pro": "🧠 Deep reasoning (pro)",
}

DEFAULT_MODEL = "gemini-2.5-flash"

# --- Debate Presets --------------------------------------------------------
TIMER_PRESETS = [30, 60, 120, 240, 300]  # seconds
MESSAGE_LIMIT_OPTIONS = [1, 2, 999]  # 999 = unlimited

# --- System Prompts --------------------------------------------------------
SYSTEM_PROMPT_COUNTER = """You are a witty, competitive tech debate judge.
When a user makes an argument, craft a sharp, factual counter-argument.
Focus on technical accuracy, hardware/software specs, and logical flaws.
Be entertaining but never self-aggrandizing. No CEO energy, no ego.
Keep counter-arguments concise (2-3 sentences max)."""

SYSTEM_PROMPT_SPORTSCASTER = """You are a live sports commentator for a tech debate.
Your job is to hyype up great arguments, roast weak takes, and react like a TV commentator.
Do NOT take sides or make debater arguments. Just commentary: "Ohhh, that's a fact check!"
Keep it short, fun, and reactive. No lengthy essays—max 1-2 sentences per comment."""

SYSTEM_PROMPT_JUDGE = """You are a brutally honest, witty tech judge.
Review all arguments and evidence. Fact-check every claim against real specs.
Score each debater on: Logic, Technical Accuracy, Counter-Quality, Evidence.
Be fair, entertaining, and unbiased. No ego, no glaze.
Output structured scoring (each category /10), then declare a winner with a 1-2 sentence justification."""

# --- Logging ---------------------------------------------------------------
def setup_logging():
    """Configure dual logging: file + console."""
    logger = logging.getLogger("debate_bot")
    logger.setLevel(logging.INFO)

    # File handler (RotatingFileHandler for Pella)
    file_handler = logging.handlers.RotatingFileHandler(
        "bot_activity.log", maxBytes=5*1024*1024, backupCount=3
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

# --- Privacy Mode Guide (for /start) ----------------------------------------
PRIVACY_MODE_GUIDE = """
🔒 **TELEGRAM PRIVACY MODE SETUP**

To allow the bot to read all group messages (required for debates):

1. Open Telegram, search for **@BotFather**
2. Send `/setprivacy`
3. Select your bot
4. Choose **Disable**
5. Add the bot to your group and make it an **admin**

Now the bot can see all messages without users mentioning it.
"""
