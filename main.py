import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
HELIUS_KEY     = os.getenv("HELIUS_KEY", "")
TIMEOUT        = 15

if not TELEGRAM_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN env var.")
if not HELIUS_KEY:
    raise RuntimeError("Missing HELIUS_KEY env var.")

HELius_META_URL = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_KEY}"

def fetch_token_metadata(mint: str):
    """
    Helius tokens/metadata :
    POST body = {"mintAccounts": ["<mint>"]}
    Retourne le 1er élément (dict) ou lève une exception explicite.
    """
    try:
        r = requests.post(HELius_META_URL, json={"mintAccounts": [mint]}, timeout=TIMEOUT)
    except Exception as e:
        raise RuntimeError(f"HTTP error to Helius: {e}")

    if r.status_code != 200:
        # Helius renvoie parfois du texte en cas d'erreur → on tronque
        raise RuntimeError(f"Helius HTTP {r.status_code}: {r.text[:140]}")

    try:
        data = r.json()
    except Exception:
        raise RuntimeError("Invalid JSON from Helius.")

    if not isinstance(data, list) or len(data) == 0:
        raise RuntimeError("No metadata found for this mint.")

    return data[0]

def pretty_bool_none(flag, ok_txt, bad_txt):
    # None = inconnu ; False/None d'authority = renounced/none (OK)
    if flag is None:
        return "❓ Inconnu"
    return ok_txt if not flag else bad_txt

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send /scan <mint> to check a token (Helius only).")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ Usage: /scan <mint>")

    mint = context.args[0].strip()

    # Optionnel : indication Pump.fun si l'adresse finit par "pump"
    is_pump = mint.endswith("pump")

    try:
        meta = fetch_token_metadata(mint)

        # name/symbol
        onchain = meta.get("onChainMetadata", {}).get("metadata", {}).get("data", {}) or {}
        name   = onchain.get("name") or meta.get("tokenInfo", {}).get("name") or "Unknown"
        symbol = onchain.get("symbol") or meta.get("tokenInfo", {}).get("symbol") or "N/A"

        # authorities (None = renounced/none)
        mint_auth   = meta.get("mintAuthority", None)
        freeze_auth = meta.get("freezeAuthority", None)

        # rendu simple
        lines = [
            "🔍 *RugCheck — Metadata (Helius)*",
            f"Mint: `{mint}`",
            "",
            f"🏷️ Token: *{name}* ({symbol}){' — Pump.fun' if is_pump else ''}",
            f"🔒 Mint authority: {pretty_bool_none(mint_auth, 'Renounced ✅', 'Active ❌')}",
            f"❄️ Freeze authority: {pretty_bool_none(freeze_auth, 'None ✅', 'Active ❌')}",
        ]

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching metadata: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.run_polling()

if __name__ == "__main__":
    main()
