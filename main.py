import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HELIUS_KEY = os.getenv("HELIUS_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send /scan <mint> to check a token.")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /scan <mint>")
        return
    mint = context.args[0]

    # --- Step 1: metadata from Helius ---
    url = f"https://api.helius.xyz/v0/token-metadata?api-key={HELIUS_KEY}"
    try:
        r = requests.post(url, json=[mint], timeout=10)
        data = r.json()[0]
        name = data.get("onChainMetadata", {}).get("metadata", {}).get("data", {}).get("name", "Unknown")
        symbol = data.get("onChainMetadata", {}).get("metadata", {}).get("data", {}).get("symbol", "N/A")
        mint_auth = data.get("mintAuthority")
        freeze_auth = data.get("freezeAuthority")

        msg = f"""
🔍 RugCheck Report
Mint: `{mint}`

🏷️ Token: {name} ({symbol})
🔒 Mint authority: {"Renounced ✅" if not mint_auth else "Active ❌"}
❄️ Freeze authority: {"None ✅" if not freeze_auth else "Active ❌"}

📊 (More checks coming soon…)
"""
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching metadata: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.run_polling()

if __name__ == "__main__":
    main()
