# ⚡ Quick Start (5 Minutes)

## 1️⃣ Get Tokens (2 min)

**Telegram:**
- DM `@BotFather` on Telegram
- Send `/newbot` → follow prompts → copy token

**Gemini:**
- Go to [aistudio.google.com](https://aistudio.google.com)
- Click "Get API Key" → copy key

## 2️⃣ Local Setup (2 min)

```bash
git clone <your-repo>
cd telegram-debate-bot

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env, paste your tokens
```

## 3️⃣ Run (1 min)

```bash
python bot.py
```

Open Telegram → find your bot → `/start`

## ✅ Done!

Try these commands:
- `/panel` - Configure & start debate
- `/topic custom whatever` - Set custom topic
- `/cancel` - Stop debate
- `/getlogs` - Download logs

---

## 🚀 Deploy to Railway (Recommended)

```bash
git push origin main
```

Then:

1. Go to [railway.app](https://railway.app)
2. Log in with GitHub
3. "New Project" → "Deploy from GitHub"
4. Select your repo
5. Add env vars (TELEGRAM_TOKEN, GEMINI_API_KEY)
6. Deploy
7. Done! (auto-deploys on every git push)

---

## 🆘 Troubleshooting

**Bot not responding?**
```bash
# Check logs
python bot.py
# Look for "Starting Tech Debate Bot..."
```

**Module not found?**
```bash
pip install -r requirements.txt
```

**Tokens not set?**
```bash
# Edit .env
nano .env  # or use your editor
```

**Still stuck?**
- Run `/getlogs` in Telegram to download `bot_activity.log`
- Check if Privacy Mode is disabled (@BotFather → /setprivacy → Disable)
- Verify bot is admin in the group chat

---

See **DEPLOYMENT_GUIDE.md** for full setup.
See **HOSTING_COMPARISON.md** for provider comparison.
