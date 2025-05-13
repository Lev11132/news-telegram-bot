import os
import json
import logging
import feedparser
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === Константи ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CACHE_FILE = "rss_cache.json"
RSS_FEEDS = [
    "https://www.pravda.com.ua/rss/",
    "https://www.unian.net/rss/all",
    "https://www.radiosvoboda.org/api/zrqiteuu$it",
    "http://rss.cnn.com/rss/edition.rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "http://feeds.reuters.com/reuters/topNews",
    "https://apnews.com/rss"
]

# === Ініціалізація кешу ===
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        news_cache = json.load(f)
else:
    news_cache = {}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(news_cache, f)

# === Логіка пошуку ===
def search_rss(query):
    results = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:
            link = entry.link
            if link in news_cache:
                continue
            text = f"{entry.title} {entry.get('summary', '')}".lower()
            if query.lower() in text:
                snippet = entry.get('summary', '')[:250]
                results.append(f"*{entry.title}*\n_{snippet.strip()}_\n[Читати]({link})")
                news_cache[link] = True
            if len(results) >= 3:
                break
        if len(results) >= 3:
            break
    save_cache()
    return results

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Напиши одне або кілька слів через кому — і я знайду згадки в останніх новинах.")

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    keywords = [k.strip() for k in text.split(",") if k.strip()]
    if not keywords:
        await update.message.reply_text("Надішли хоча б одне слово.")
        return

    all_results = []
    for keyword in keywords:
        matches = search_rss(keyword)
        if matches:
            all_results.append(f"*Запит:* `{keyword}`\n" + "\n\n".join(matches))
        else:
            all_results.append(f"*Запит:* `{keyword}`\n_Нічого не знайдено._")

    for block in all_results:
        await update.message.reply_text(block, parse_mode="Markdown", disable_web_page_preview=True)

# === Запуск бота ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
    app.run_polling()

if __name__ == "__main__":
    main()