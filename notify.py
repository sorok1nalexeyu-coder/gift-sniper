import os
import json
import time
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)
DATA_DIR = os.getenv("DATA_DIR", "/data")
EVENTS_PATH = os.path.join(DATA_DIR, "events.json")

class Notifier:
    def __init__(self, config: dict):
        self.webhook = config.get("notification_webhook")
        self.tg_token = config.get("notification_bot_token")
        self.tg_chat_id = config.get("notification_chat_id")
        self.channels = config.get("ultra_rare_alert_channels", ["telegram", "webhook"])

    async def send(self, title: str, message: str, level: str = "info"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        event = {"ts": timestamp, "level": level, "title": title, "message": message}
        logger.info(f"📢 [{level.upper()}] {title}: {message}")
        self._save_event(event)

        if "webhook" in self.channels and self.webhook:
            try:
                async with httpx.AsyncClient() as c:
                    await c.post(self.webhook, json=event, timeout=5)
            except Exception as e:
                logger.error(f"❌ Webhook error: {e}")

        if "telegram" in self.channels and self.tg_token and self.tg_chat_id:
            text = f"🎁 <b>{title}</b>\n{message}\n🕒 {timestamp}"
            url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            try:
                async with httpx.AsyncClient() as c:
                    await c.post(url, json={"chat_id": self.tg_chat_id, "text": text, "parse_mode": "HTML"}, timeout=5)
            except Exception as e:
                logger.error(f"❌ TG Notify error: {e}")

    def _save_event(self, event: dict):
        try:
            events = []
            if os.path.exists(EVENTS_PATH):
                with open(EVENTS_PATH, "r", encoding="utf-8") as f:
                    events = json.load(f)
            events.append(event)
            events = events[-500:]
            with open(EVENTS_PATH, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error saving event: {e}")
