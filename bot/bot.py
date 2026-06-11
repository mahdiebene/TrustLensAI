"""TrustLens Telegram Bot.


A self-contained, dependency-light Telegram bot that lets users verify the
credibility of any text, link, or forwarded post using the TrustLens backend.

Features
--------
- Commands: /start, /help, /about, /lang
- Analyze plain text, URLs, or forwarded messages
- /analyze <text> explicit command
- Per-chat language preference (Bangla default, English toggle)
- Typing indicator + "analyzing" feedback
- Rich, safe HTML-formatted results (score badge, verdict, pillar bars,
  explanation, link to the full web report)
- Graceful handling of scrape failures and backend/network errors
- Robust long-polling loop with offset tracking and back-off

Environment
-----------
- TELEGRAM_BOT_TOKEN  (required) — token from @BotFather
- API_URL             (optional) — TrustLens backend base URL
                                    (default: http://localhost:8000)
- APP_URL             (optional) — public web app URL for "full report" links
                                    (default: https://trust-lens-ai-beta.vercel.app)


Run
---
    python bot/bot.py
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import sys
from typing import Any
from urllib.parse import quote

import httpx


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
APP_URL = os.getenv("APP_URL", "https://trust-lens-ai-beta.vercel.app").rstrip("/")
# Cap deep-link query length so the "full report" URL stays well within
# Telegram/browser limits; the frontend re-runs analysis from the `content` param.
MAX_DEEPLINK_CONTENT = 1500

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Timeouts (seconds)
LONG_POLL_TIMEOUT = 30
ANALYZE_TIMEOUT = 90.0
SEND_TIMEOUT = 15.0

# Telegram hard limit is 4096 chars per message.
MAX_MESSAGE_LEN = 3800
# Backend caps content at 10000 chars; trim before sending to avoid 422.
MAX_CONTENT_LEN = 9000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("trustlens.bot")

# In-memory per-chat language preference. "bn" (default) or "en".
_chat_lang: dict[int, str] = {}


# ---------------------------------------------------------------------------
# Localized copy
# ---------------------------------------------------------------------------

COPY: dict[str, dict[str, str]] = {
    "bn": {
        "welcome": (
            "<b>🔍 TrustLens — বিশ্বাসযোগ্যতা যাচাই</b>\n\n"
            "গুজব চিনুন, সত্য জানুন।\n\n"
            "<b>যেভাবে ব্যবহার করবেন:</b>\n"
            "• যেকোনো খবর, পোস্ট বা মেসেজ এখানে পাঠান (বা ফরওয়ার্ড করুন)\n"
            "• লিংক পাঠালে আমরা সেটি যাচাই করব\n"
            "• অথবা <code>/analyze লেখা</code> কমান্ড ব্যবহার করুন\n\n"
            "<b>কমান্ড:</b>\n"
            "/help — সাহায্য\n"
            "/about — TrustLens সম্পর্কে\n"
            "/lang — ভাষা পরিবর্তন (English/বাংলা)"
        ),
        "help": (
            "<b>ℹ️ সাহায্য</b>\n\n"
            "যেকোনো লেখা, খবরের লিংক বা সোশ্যাল মিডিয়া পোস্ট পাঠান — "
            "আমি ৬টি বিশ্বাসযোগ্যতা স্তম্ভ বিশ্লেষণ করে একটি স্কোর দেব।\n\n"
            "<b>উদাহরণ:</b>\n"
            "• <code>/analyze আজ ঢাকায় ভূমিকম্প হয়েছে</code>\n"
            "• একটি খবরের লিংক পাঠান\n"
            "• কোনো মেসেজ ফরওয়ার্ড করুন\n\n"
            "ভাষা বদলাতে /lang ব্যবহার করুন।"
        ),
        "about": (
            "<b>🔍 TrustLens সম্পর্কে</b>\n\n"
            "TrustLens বাংলা ও ইংরেজি কনটেন্টের বিশ্বাসযোগ্যতা যাচাই করে — "
            "AI ও ৬টি বিশ্লেষণ স্তম্ভ ব্যবহার করে।\n\n"
            "🌐 ওয়েব: {app}\n"
            "এটি কোনো চূড়ান্ত রায় নয় — সবসময় একাধিক নির্ভরযোগ্য সূত্র যাচাই করুন।"
        ),
        "lang_set": "✅ ভাষা বাংলায় সেট করা হয়েছে।",
        "analyzing": "🔍 বিশ্লেষণ চলছে, একটু অপেক্ষা করুন...",
        "empty_analyze": "⚠️ যাচাই করার জন্য কিছু লেখা দিন।\nউদাহরণ: <code>/analyze লেখা</code>",
        "too_short": "⚠️ যাচাই করার জন্য আরও কিছু লেখা পাঠান (অন্তত কয়েকটি শব্দ)।",
        "photo_only": (
            "📷 ছবি পেয়েছি, তবে এই মুহূর্তে আমি ছবির সাথে থাকা লেখা বা ক্যাপশন যাচাই করি। "
            "অনুগ্রহ করে দাবিটি লিখে পাঠান অথবা সংশ্লিষ্ট লিংক দিন।"
        ),
        "error": "❌ বিশ্লেষণ করা যায়নি। কিছুক্ষণ পর আবার চেষ্টা করুন।",
        "score": "বিশ্বাসযোগ্যতা স্কোর",
        "verdict": "রায়",
        "pillars": "স্তম্ভভিত্তিক স্কোর",
        "full_report": "🌐 বিস্তারিত রিপোর্ট দেখুন",
        "scrape_failed": (
            "⚠️ লিংকটি থেকে কনটেন্ট আনা যায়নি।\n"
            "অনুগ্রহ করে পোস্টের লেখাটি কপি করে পাঠান।"
        ),
    },
    "en": {
        "welcome": (
            "<b>🔍 TrustLens — Credibility Checker</b>\n\n"
            "See through the noise. Trust what matters.\n\n"
            "<b>How to use:</b>\n"
            "• Send (or forward) any news, post, or message here\n"
            "• Send a link and we'll verify it\n"
            "• Or use <code>/analyze your text</code>\n\n"
            "<b>Commands:</b>\n"
            "/help — Help\n"
            "/about — About TrustLens\n"
            "/lang — Change language (English/বাংলা)"
        ),
        "help": (
            "<b>ℹ️ Help</b>\n\n"
            "Send any text, news link, or social media post — I'll analyze it "
            "across 6 trust pillars and give you a credibility score.\n\n"
            "<b>Examples:</b>\n"
            "• <code>/analyze An earthquake hit Dhaka today</code>\n"
            "• Send a news link\n"
            "• Forward any message\n\n"
            "Use /lang to switch language."
        ),
        "about": (
            "<b>🔍 About TrustLens</b>\n\n"
            "TrustLens verifies the credibility of Bangla and English content "
            "using AI across 6 analysis pillars.\n\n"
            "🌐 Web: {app}\n"
            "This is not a final verdict — always cross-check trustworthy sources."
        ),
        "lang_set": "✅ Language set to English.",
        "analyzing": "🔍 Analyzing, please wait...",
        "empty_analyze": "⚠️ Please provide text to analyze.\nExample: <code>/analyze your text</code>",
        "too_short": "⚠️ Please send a bit more text to analyze (at least a few words).",
        "photo_only": (
            "📷 I received a photo, but right now I analyze text or captions. "
            "Please type the claim, or send the related link."
        ),
        "error": "❌ Couldn't complete the analysis. Please try again shortly.",
        "score": "Trust Score",
        "verdict": "Verdict",
        "pillars": "Pillar Scores",
        "full_report": "🌐 View full report",
        "scrape_failed": (
            "⚠️ Couldn't fetch content from that link.\n"
            "Please copy and send the post's text instead."
        ),
    },
}


def t(chat_id: int, key: str) -> str:
    """Return localized copy for a chat."""
    lang = _chat_lang.get(chat_id, "bn")
    return COPY.get(lang, COPY["bn"]).get(key, COPY["en"].get(key, key))


# ---------------------------------------------------------------------------
# Telegram API helpers
# ---------------------------------------------------------------------------


async def _tg_post(client: httpx.AsyncClient, method: str, payload: dict) -> dict | None:
    """POST to the Telegram Bot API and return the parsed JSON (or None)."""
    try:
        resp = await client.post(
            f"{TELEGRAM_API}/{method}",
            json=payload,
            timeout=SEND_TIMEOUT,
        )
        data = resp.json()
        if not data.get("ok"):
            logger.warning("Telegram %s failed: %s", method, data.get("description"))
        return data
    except Exception as exc:  # noqa: BLE001 - network resilience
        logger.error("Telegram %s error: %s", method, exc)
        return None


async def send_message(
    client: httpx.AsyncClient,
    chat_id: int,
    text: str,
    *,
    disable_preview: bool = True,
) -> None:
    """Send an HTML message, splitting if it exceeds Telegram's length limit."""
    for chunk in _split_message(text):
        await _tg_post(
            client,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": disable_preview,
            },
        )


async def send_chat_action(client: httpx.AsyncClient, chat_id: int, action: str = "typing") -> None:
    """Show a chat action (e.g. 'typing') to signal work in progress."""
    await _tg_post(client, "sendChatAction", {"chat_id": chat_id, "action": action})


def _split_message(text: str) -> list[str]:
    """Split a long message into Telegram-sized chunks on line boundaries."""
    if len(text) <= MAX_MESSAGE_LEN:
        return [text]
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_MESSAGE_LEN:
            if current:
                chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


# ---------------------------------------------------------------------------
# Backend integration
# ---------------------------------------------------------------------------


async def analyze_content(content: str) -> dict:
    """Call the TrustLens backend to analyze content. Returns dict (may hold 'error')."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_URL}/api/analyze",
                json={"content": content[:MAX_CONTENT_LEN]},
                timeout=ANALYZE_TIMEOUT,
            )
        if resp.status_code == 200:
            return resp.json()
        logger.warning("Backend returned %s: %s", resp.status_code, resp.text[:200])
        return {"error": f"API returned {resp.status_code}"}
    except httpx.TimeoutException:
        return {"error": "timeout"}
    except Exception as exc:  # noqa: BLE001 - network resilience
        logger.error("Analyze error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------


def _score_emoji(score: float) -> str:
    if score >= 80:
        return "✅"
    if score >= 60:
        return "🟢"
    if score >= 40:
        return "🟡"
    if score >= 20:
        return "🟠"
    return "🔴"


def _score_bar(score: float, width: int = 10) -> str:
    """Render a unicode progress bar for a 0-100 score."""
    filled = max(0, min(width, round(score / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def _esc(text: str) -> str:
    """HTML-escape user/model text for safe HTML parse mode."""
    return html.escape(text or "", quote=False)


def _report_url(content: str = "") -> str:
    """Build a deep link to the full web report for the given content.

    The frontend `/results` page re-runs analysis from the `content` query
    param (served from the backend cache, so it loads instantly). Falls back
    to the app home if there's no content to link.
    """
    snippet = (content or "").strip()
    if not snippet:
        return APP_URL
    return f"{APP_URL}/results?content={quote(snippet[:MAX_DEEPLINK_CONTENT])}"


def format_result(chat_id: int, result: dict, content: str = "") -> str:
    """Format an analysis result into a localized HTML message."""
    lang = _chat_lang.get(chat_id, "bn")

    # Scrape failure → ask user for text.

    if result.get("scrape_failed"):
        reason = result.get("scrape_reason_bn" if lang == "bn" else "scrape_reason_en", "")
        msg = t(chat_id, "scrape_failed")
        if reason:
            msg += f"\n\n<i>{_esc(reason)}</i>"
        return msg

    score = float(result.get("trust_score", 0) or 0)
    verdict = result.get("verdict_bn" if lang == "bn" else "verdict", "") or result.get("verdict", "")
    explanation = (
        result.get("explanation_bn" if lang == "bn" else "explanation_en", "")
        or result.get("explanation_en", "")
    )

    emoji = _score_emoji(score)
    lines = [
        "<b>🔍 TrustLens</b>",
        "",
        f"<b>{t(chat_id, 'score')}:</b> {emoji} <b>{score:.0f}</b>/100",
        f"<code>{_score_bar(score)}</code>",
    ]
    if verdict:
        lines.append(f"<b>{t(chat_id, 'verdict')}:</b> {_esc(verdict)}")
    lines.append("")

    # Pillar breakdown (active only, weakest first to surface concerns).
    pillars = [p for p in result.get("pillars", []) if p.get("active", True)]
    if pillars:
        lines.append(f"<b>{t(chat_id, 'pillars')}:</b>")
        for p in sorted(pillars, key=lambda x: x.get("score", 0)):
            name = p.get("name_bn" if lang == "bn" else "name") or p.get("name", "")
            p_score = float(p.get("score", 0) or 0)
            lines.append(
                f"{_score_emoji(p_score)} {_esc(name)} — "
                f"<code>{_score_bar(p_score, 6)}</code> {p_score:.0f}"
            )
        lines.append("")

    # Overall explanation (trimmed).
    if explanation:
        snippet = explanation.strip()
        if len(snippet) > 600:
            snippet = snippet[:600].rstrip() + "…"
        lines.append(f"<i>{_esc(snippet)}</i>")
        lines.append("")

    # Link to the full web report (deep link re-runs the same analysis).
    lines.append(f'<a href="{_report_url(content)}">{t(chat_id, "full_report")}</a>')


    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command + message handling
# ---------------------------------------------------------------------------


def _extract_text(message: dict) -> str:
    """Pull the most relevant text from a message (text or photo caption)."""
    return (message.get("text") or message.get("caption") or "").strip()


async def handle_command(
    client: httpx.AsyncClient, chat_id: int, text: str
) -> bool:
    """Handle a /command. Returns True if the message was a handled command."""
    cmd = text.split()[0].lower()
    # Strip @BotName suffix for group mentions (e.g. /start@TrustLensBot).
    cmd = cmd.split("@", 1)[0]

    if cmd == "/start":
        await send_message(client, chat_id, t(chat_id, "welcome"))
        return True

    if cmd == "/help":
        await send_message(client, chat_id, t(chat_id, "help"))
        return True

    if cmd == "/about":
        await send_message(client, chat_id, t(chat_id, "about").format(app=APP_URL))
        return True

    if cmd == "/lang":
        # Toggle, or honor an explicit argument: /lang en | /lang bn
        arg = text[len(cmd):].strip().lower()
        if arg in ("en", "english"):
            new_lang = "en"
        elif arg in ("bn", "bangla", "bengali", "বাংলা"):
            new_lang = "bn"
        else:
            new_lang = "en" if _chat_lang.get(chat_id, "bn") == "bn" else "bn"
        _chat_lang[chat_id] = new_lang
        await send_message(client, chat_id, t(chat_id, "lang_set"))
        return True

    if cmd == "/analyze":
        content = text[len(cmd):].strip()
        if not content:
            await send_message(client, chat_id, t(chat_id, "empty_analyze"))
            return True
        await run_analysis(client, chat_id, content)
        return True

    return False


async def run_analysis(client: httpx.AsyncClient, chat_id: int, content: str) -> None:
    """Analyze content and reply with a formatted result."""
    if len(content) < 3:
        await send_message(client, chat_id, t(chat_id, "too_short"))
        return

    await send_chat_action(client, chat_id, "typing")
    await send_message(client, chat_id, t(chat_id, "analyzing"))

    result = await analyze_content(content)
    if "error" in result:
        await send_message(client, chat_id, t(chat_id, "error"))
        return

    await send_message(
        client, chat_id, format_result(chat_id, result, content), disable_preview=False
    )



async def handle_update(client: httpx.AsyncClient, update: dict[str, Any]) -> None:
    """Route a single Telegram update."""
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if chat_id is None:
        return

    text = _extract_text(message)

    # Photo without any caption → we can't analyze pixels yet.
    if not text and message.get("photo"):
        await send_message(client, chat_id, t(chat_id, "photo_only"))
        return

    if not text:
        return

    # Commands start with "/".
    if text.startswith("/"):
        handled = await handle_command(client, chat_id, text)
        if handled:
            return
        # Unknown command → fall through and analyze it as text.

    await run_analysis(client, chat_id, text)


# ---------------------------------------------------------------------------
# Startup + polling
# ---------------------------------------------------------------------------


async def register_commands(client: httpx.AsyncClient) -> None:
    """Register the bot's command menu with Telegram."""
    await _tg_post(
        client,
        "setMyCommands",
        {
            "commands": [
                {"command": "start", "description": "Start / শুরু করুন"},
                {"command": "analyze", "description": "Analyze text / যাচাই করুন"},
                {"command": "lang", "description": "Switch language / ভাষা পরিবর্তন"},
                {"command": "help", "description": "Help / সাহায্য"},
                {"command": "about", "description": "About / সম্পর্কে"},
            ]
        },
    )


async def poll_updates() -> None:
    """Long-poll Telegram for updates and dispatch them."""
    offset = 0
    logger.info("Starting long-poll loop (API_URL=%s)…", API_URL)

    async with httpx.AsyncClient() as client:
        await register_commands(client)
        # Drop any backlog so we don't replay old messages on restart.
        try:
            resp = await client.get(
                f"{TELEGRAM_API}/getUpdates",
                params={"offset": -1, "timeout": 0},
                timeout=10.0,
            )
            results = resp.json().get("result", [])
            if results:
                offset = results[-1]["update_id"] + 1
        except Exception:  # noqa: BLE001
            pass

        backoff = 1
        while True:
            try:
                resp = await client.get(
                    f"{TELEGRAM_API}/getUpdates",
                    params={"offset": offset, "timeout": LONG_POLL_TIMEOUT},
                    timeout=LONG_POLL_TIMEOUT + 10,
                )
                data = resp.json()
                if not data.get("ok"):
                    logger.warning("getUpdates not ok: %s", data.get("description"))
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 30)
                    continue

                backoff = 1
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    try:
                        await handle_update(client, update)
                    except Exception as exc:  # noqa: BLE001 - never crash the loop
                        logger.error("handle_update error: %s", exc)

            except httpx.TimeoutException:
                # Normal for long-polling when no updates arrive.
                continue
            except Exception as exc:  # noqa: BLE001 - network resilience
                logger.error("Polling error: %s", exc)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)


def main() -> None:
    """Entry point for the TrustLens Telegram bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Aborting.")
        sys.exit(1)

    logger.info("TrustLens Telegram Bot starting…")
    try:
        asyncio.run(poll_updates())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")


if __name__ == "__main__":
    main()
