"""TrustLens Telegram Bot.

Commands:
  /start - Welcome message in Bengali + English
  /analyze <text> - Analyze content
  Forward any message - Auto-analyze

Uses the same backend API for analysis.
"""

import asyncio
import logging
import os
import sys
import httpx

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_message(chat_id: int, text: str, parse_mode: str = "HTML") -> None:
    """Send a message to a Telegram chat."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            },
            timeout=10.0,
        )


async def analyze_content(content: str) -> dict:
    """Call the TrustLens API to analyze content."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/analyze",
            json={"content": content},
            timeout=60.0,
        )
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned {response.status_code}"}


def format_score_badge(score: float) -> str:
    """Format score as a visual badge."""
    if score >= 80:
        return f"✅ {score:.0f}/100"
    elif score >= 60:
        return f"⚠️ {score:.0f}/100"
    elif score >= 40:
        return f"⚠️⚠️ {score:.0f}/100"
    elif score >= 20:
        return f"❌ {score:.0f}/100"
    else:
        return f"🚨 {score:.0f}/100"


def format_result(result: dict) -> str:
    """Format analysis result for Telegram."""
    if "error" in result:
        return f"❌ Analysis failed: {result['error']}"

    score = result.get("trust_score", 0)
    verdict = result.get("verdict", "Unknown")
    verdict_bn = result.get("verdict_bn", "")
    explanation_bn = result.get("explanation_bn", "")
    explanation_en = result.get("explanation_en", "")

    badge = format_score_badge(score)

    # Build message
    lines = [
        f"<b>🔍 TrustLens বিশ্লেষণ</b>",
        f"",
        f"<b>বিশ্বাসযোগ্যতা স্কোর:</b> {badge}",
        f"<b>রায়:</b> {verdict_bn}",
        f"",
    ]

    # Top 3 pillar findings
    pillars = result.get("pillars", [])
    active_pillars = [p for p in pillars if p.get("active")]
    if active_pillars:
        lines.append("<b>স্তম্ভ স্কোর:</b>")
        for p in sorted(active_pillars, key=lambda x: x["score"])[:3]:
            p_badge = format_score_badge(p["score"])
            lines.append(f"  • {p.get('name_bn', p['name'])}: {p_badge}")
        lines.append("")

    # Explanation
    if explanation_bn:
        lines.append(f"<i>{explanation_bn[:300]}</i>")
    elif explanation_en:
        lines.append(f"<i>{explanation_en[:300]}</i>")

    lines.append(f"\n⏱ {result.get('processing_time_ms', 0)}ms")

    return "\n".join(lines)


async def handle_start(chat_id: int) -> None:
    """Handle /start command."""
    welcome = (
        "<b>🔍 TrustLens — বিশ্বাসযোগ্যতা যাচাই</b>\n\n"
        "গুজব চিনুন, সত্য জানুন।\n"
        "See through the noise. Trust what matters.\n\n"
        "<b>ব্যবহার:</b>\n"
        "• যেকোনো পোস্ট বা মেসেজ ফরওয়ার্ড করুন\n"
        "• অথবা /analyze কমান্ড দিয়ে টেক্সট পাঠান\n"
        "• অথবা সরাসরি টেক্সট/লিংক পাঠান\n\n"
        "<b>Usage:</b>\n"
        "• Forward any message to analyze\n"
        "• Use /analyze followed by text\n"
        "• Or just send text/URL directly"
    )
    await send_message(chat_id, welcome)


async def handle_message(update: dict) -> None:
    """Handle incoming message."""
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return

    # Handle commands
    if text.startswith("/start"):
        await handle_start(chat_id)
        return

    if text.startswith("/analyze"):
        content = text[8:].strip()
        if not content:
            await send_message(chat_id, "⚠️ Please provide text to analyze.\nউদাহরণ: /analyze <টেক্সট>")
            return
    else:
        # Treat any non-command message as content to analyze
        content = text

    # Send "analyzing" message
    await send_message(chat_id, "🔍 বিশ্লেষণ চলছে... Analyzing...")

    # Call API
    result = await analyze_content(content)
    response_text = format_result(result)
    await send_message(chat_id, response_text)


async def poll_updates() -> None:
    """Long-poll for Telegram updates."""
    offset = 0
    logger.info("[Bot] Starting long-poll loop...")

    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(
                    f"{TELEGRAM_API}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                    timeout=35.0,
                )
                data = response.json()

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    await handle_message(update)

            except Exception as e:
                logger.error(f"[Bot] Polling error: {e}")
                await asyncio.sleep(5)


def main():
    """Entry point for the Telegram bot."""
    if not BOT_TOKEN:
        logger.error("[Bot] TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    logger.info(f"[Bot] Starting TrustLens Telegram Bot")
    logger.info(f"[Bot] API URL: {API_URL}")
    asyncio.run(poll_updates())


if __name__ == "__main__":
    main()
