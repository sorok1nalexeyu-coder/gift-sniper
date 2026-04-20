import os
import sys
import asyncio
import logging
from telethon import TelegramClient
from config_manager import ConfigManager
from ui import SetupUI
from sniper import GiftSniper

DATA_DIR = os.getenv("DATA_DIR", ".")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(DATA_DIR, "sniper.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    cfg_mgr = ConfigManager()

    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        SetupUI(cfg_mgr).run_setup()
        return

    c = cfg_mgr.config
    if not c["api_id"] or not c["api_hash"]:
        logger.error("❌ Запустите `python main.py --setup` для настройки")
        return

    session = os.path.join(DATA_DIR, "gift_sniper_session")
    client = TelegramClient(session, c["api_id"], c["api_hash"], device_model="GiftSniper", system_version="Linux")
    await client.start(phone=c["phone"])
    me = await client.get_me()
    logger.info(f"✅ Авторизован: {me.first_name} (@{me.username})")

    sniper = GiftSniper(client)
    try:
        await sniper.monitor()
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка...")
        sniper.stop()
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
