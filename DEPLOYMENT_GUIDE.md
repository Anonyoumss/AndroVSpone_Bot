# 🚀 DEPLOYMENT GUIDE - Tech Debate Bot

## Quick Start (5 minutes)

### 1. Get Your Tokens

**Telegram Bot Token:**
- Message `@BotFather` on Telegram
- Send `/newbot`, follow prompts, copy the token

**Gemini API Key:**
- Go to [aistudio.google.com](https://aistudio.google.com)
- Click **Get API key**, create new project, copy the key

### 2. Clone & Setup

```bash
git clone <repo-url>
cd telegram-debate-bot

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and paste your TELEGRAM_TOKEN and GEMINI_API_KEY
```

### 3. Run Locally

```bash
python bot.py
```

You'll see:
```
2026-09-27 18:11:05 | INFO | 🚀 Starting Tech Debate Bot...
```

Go to Telegram, find your bot, send `/start`.

---

## 🌍 Hosting: Easy Alternatives to Pella

**Pella** works but isn't ideal for persistent bots. Here are better free/cheap options:

### **1. 🥇 RAILWAY** (Recommended - Best Balance)

**Pros:**
- Free $5/month credit (plenty for a small bot)
- Dead simple GitHub integration
- Auto-deploy on git push
- No cold starts (unlike Render)

**Cons:**
- Credit runs out (but $5/month is ~$50/month usage)

**Setup (2 minutes):**

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click **New Project** → **Deploy from GitHub repo**
4. Select your bot repo
5. Add environment variables:
   - `TELEGRAM_TOKEN=...`
   - `GEMINI_API_KEY=...`
6. Click **Deploy**
7. Your bot is live!

**Cost:** $5/month free → $0.50 per machine-hour after

---

### **2. 🔵 RENDER** (Free, But Slower)

**Pros:**
- Completely free
- No credit card needed
- Good for testing

**Cons:**
- Spins down after 15 min idle (slow startup)
- Limited to 0.5GB RAM

**Setup:**

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click **New** → **Web Service**
4. Connect your GitHub repo
5. Set start command: `python bot.py`
6. Add env vars
7. Deploy

**Cost:** Free

---

### **3. 🔴 ORACLE CLOUD** (Most Generous Free Tier)

**Pros:**
- Always-free VM (1 OCPU, 1GB RAM)
- No time limits, no cold starts
- Genuinely free forever

**Cons:**
- More setup (SSH, terminal, Linux knowledge)
- Need credit card (but won't charge)

**Setup (10 minutes):**

1. Sign up at [oracle.com/cloud/free](https://www.oracle.com/cloud/free/)
2. Create a **Compute Instance** (Ubuntu, free tier eligible)
3. SSH into your instance
4. Clone repo, install Python, run bot:
   ```bash
   git clone <repo-url>
   cd telegram-debate-bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Run in background with nohup
   nohup python bot.py > bot.log 2>&1 &
   ```
5. Bot runs 24/7 for free

**Cost:** Free

---

### **4. ⚫ VERCEL** (Not Recommended for Long-Polling Bots)

**Why?** Vercel is for serverless functions, not persistent bots. Telegram bots need long-polling or webhooks, which Vercel doesn't support well.

---

## 📊 Comparison

| Platform | Cost | Setup | Cold Start | Persistence |
|----------|------|-------|-----------|------------|
| **Railway** | $5/mo free | 2 min | None | ✅ 24/7 |
| **Render** | Free | 3 min | 15s delay | ⚠️ Sleeps idle |
| **Oracle** | Free | 10 min | None | ✅ 24/7 |
| **Pella** | Free | 2 min | None | ⚠️ Restarts |

---

## 🎯 My Recommendation

**For you:** Use **Railway**

- ✅ Dead simple setup (click → deploy)
- ✅ No cold starts (bot always responsive)
- ✅ $5/month free credit lasts long
- ✅ One-click rollback if something breaks
- ✅ Live logs in dashboard

---

## 📝 Setting Up on Railway (Step-by-Step)

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/telegram-debate-bot.git
git push -u origin main
```

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Log in with GitHub
3. Click **New Project** → **Deploy from GitHub repo**
4. Authorize Railway to access your repos
5. Select `telegram-debate-bot`
6. Choose **Python** as runtime

### Step 3: Add Environment Variables

In Railway dashboard:
- Click **Variables** (in your project)
- Add:
  ```
  TELEGRAM_TOKEN = your_token_here
  GEMINI_API_KEY = your_key_here
  ```

### Step 4: Set Start Command

- Click **Settings** in Railway
- Set **Start Command**: `python bot.py`

### Step 5: Deploy!

Railway auto-deploys. Watch the **Deploy** tab for logs.

Once you see **"🚀 Starting Tech Debate Bot..."** → Your bot is live!

---

## 🔧 Troubleshooting

**Bot not responding?**
- Check Railway logs (click **Logs** tab)
- Verify `TELEGRAM_TOKEN` and `GEMINI_API_KEY` in Variables
- Restart: click **Redeploy** button

**Logs not saving to `bot_activity.log`?**
- Railway's `/tmp` is ephemeral. For persistent logs:
  1. Download the log file with `/getlogs` command in Telegram
  2. Or, set up a simple database (SQLite in Railway's persistent storage)

**Gemini API errors?**
- Check your API key has billing enabled (free tier may have limits)
- Go to [console.cloud.google.com](https://console.cloud.google.com)
- Ensure `Generative Language API` is enabled

---

## 🛡️ Privacy Mode Setup (Required!)

After deploying, enable Privacy Mode so the bot reads all group messages:

1. Message `@BotFather` on Telegram
2. Send `/setprivacy`
3. Select your bot
4. Choose **Disable**
5. Add your bot to a group and make it **admin**

Now the bot can read all messages without users tagging it.

---

## 📊 Features Checklist

- ✅ 7 preset debate topics + custom fallback
- ✅ 3 debate modes (Human vs AI, 1v1 Silent, 1v1 Sportscaster)
- ✅ Configurable timers (30s → 300s)
- ✅ Message limits (1, 2, unlimited per person)
- ✅ Model selector (lite, flash, pro)
- ✅ Live timer bar (updates every 5s)
- ✅ Multimodal Gemini (text + photos + videos)
- ✅ Structured scoring verdict
- ✅ File-based logging with `/getlogs`
- ✅ Fair, witty AI judge (anti-glaze system prompts)

---

## 🚨 Quick Fixes

**"No module named telegram"?**
```bash
pip install -r requirements.txt
```

**"TELEGRAM_TOKEN not set"?**
```bash
# Create .env file
echo "TELEGRAM_TOKEN=your_token" > .env
echo "GEMINI_API_KEY=your_key" >> .env
```

**"Bot not reading messages in group?"**
Go to @BotFather, /setprivacy, select bot, choose Disable.

---

## 🎉 You're Done!

Your bot is now live. Try it:

```
/start           → Welcome + privacy guide
/panel           → Configure debate
/topic custom    → Set custom topic
/debate          → Start with config
/cancel          → Stop debate
/getlogs         → Download activity logs
```

Send photos/videos during debates—Gemini will analyze them!

---

## 💡 Next Steps

- **Add webhook support** (faster than long-polling)
- **Database** (SQLite for persistent state)
- **Scoring history** (track debate stats)
- **Custom AI personalities** (different judge styles)
- **Discord version** (similar architecture, different API)

---

Questions? Check the bot logs with `/getlogs` or DM the bot `/start` → /getlogs.
