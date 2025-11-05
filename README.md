## Automated Telegram News Summary Bot

Free, local-first Telegram bot that fetches news via RSS feeds and returns concise extractive summaries for user-selected topics.

> No paid APIs required. Summarization is extractive (TextRank) and runs locally.

### Features
- Topic selection via inline buttons (technology, world, business, sports, science, health, entertainment)
- Fetches from reputable RSS feeds (no paid APIs)
- Extractive summarization (TextRank) – fully free, no external LLM API
- Simple JSON storage for per-user topic preferences

### Tech stack
- Python 3.10+
- python-telegram-bot (async, v21)
- feedparser, trafilatura (fetch + extract article content)
- sumy (TextRank summarizer)
- dotenv for configuration

### Setup
1) Create a bot with BotFather and obtain your bot token.

2) Environment variables (keep secrets out of git):
   - Copy `env.sample` to `.env`
   - Set `TELEGRAM_BOT_TOKEN` in `.env`
   - Note: `.env` is ignored by `.gitignore` so your token isn’t committed

3) Create a virtual environment and install dependencies:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

4) Run the bot:
```bash
python -m src.main
```

### Usage
- `/start` to begin and choose your topics
- `/topics` to update your preferences
- `/latest` to get summarized headlines for your selected topics
 - `/help` list all commands
 - `/setlatestcount <n>` set articles per topic for `/latest` (1-10)
 - `/setdailycount <n>` set articles per topic for daily digest (1-10)
 - `/schedule <morning|evening|night>` pick your daily digest time
 - `/subscribe` start receiving the daily digest automatically
 - `/unsubscribe` stop receiving the daily digest

### Open source: how to contribute
Contributions are welcome! Please:
- Open an issue for bugs/feature requests
- Submit PRs with a clear description and minimal changes
- Keep code readable and documented where non-obvious

### Local run and dev
```bash
python -m src.main
```

### Deploy (free-friendly options)
- Render/OCI/Hetzner/Fly.io free tiers
- Use polling or set up webhooks; ensure the process stays alive

### Security notes
- Never commit `.env`; the file is ignored by default
- Rotate tokens if accidentally exposed

### License
MIT

### Notes
- Summaries are extractive using TextRank; no paid API keys are needed
- The default feed set is curated but you can add/change RSS feeds in `src/news.py`
- User preferences are stored in `data/users.json`

### Optional (free hosting suggestions)
- Fly.io, Deta Space, or Render free tiers can run this
- For hosting, add a `Procfile` and keep the process alive; also consider webhook mode instead of polling

