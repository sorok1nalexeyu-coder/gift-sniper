import os
import json
import time
import asyncio
import logging
from typing import Any
from telethon import TelegramClient
from telethon.tl import functions, types
from telethon.errors import FloodWaitError
from notify import Notifier

logger = logging.getLogger(__name__)
CONFIG_PATH = os.path.join(os.getenv("DATA_DIR", "."), "config.json")

class GiftSniper:
    def __init__(self, client: TelegramClient):
        self.client = client
        self.notifier = Notifier({})
        self.config = {}
        self.purchased = set()
        self.running = False
        self.reload_config()

    def reload_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            self.notifier = Notifier(self.config)
        except Exception as e:
            logger.error(f"❌ Ошибка чтения конфига: {e}")

    def is_collectible(self, gift: Any) -> bool:
        if not self.config.get("only_collectibles", False):
            return True
        rarity = str(getattr(gift, "rarity", "")).lower()
        is_nft = bool(getattr(gift, "is_nft", False) or getattr(gift, "is_collectible", False))
        allowed = [r.lower() for r in self.config.get("allowed_rarities", ["collectible", "nft", "legendary"])]
        return is_nft or rarity in allowed

    async def check_ultra_rare(self, gift: Any) -> bool:
        threshold = int(self.config.get("ultra_rare_threshold", 100))
        supply = int(getattr(gift, "remaining_supply", 999999))
        is_nft = bool(getattr(gift, "is_nft", False) or getattr(gift, "is_collectible", False))
        rarity = str(getattr(gift, "rarity", "")).lower()
        is_ultra = (supply <= threshold and is_nft and rarity in ("legendary", "mythic", "ultra_rare", "collectible"))
        if is_ultra:
            await self.notifier.send("🚨 ULTRA-RARE DETECTED!", 
                f"#{getattr(gift, 'id', '?')} | {getattr(gift, 'name', '?')} | Тираж: {supply} | Цена: {getattr(gift, 'price', 0)}⭐", "error")
            return True
        return False

    async def fetch_gifts(self) -> list:
        try:
            res = await self.client(functions.messages.GetFeaturedStickersRequest())
            gifts = []
            for s in getattr(res, "sets", []):
                if hasattr(s, "gift") or "gift" in str(s).lower():
                    gifts.append(s)
            return gifts
        except Exception as e:
            logger.error(f"⚠️ Ошибка получения подарков: {e}")
            return []

    async def fetch_auctions(self) -> list:
        try:
            res = await self.client.invoke(functions.messages.GetFeaturedGiftsRequest(offset=0, limit=100, hash=0))
            auctions = []
            for item in getattr(res, "auctions", []) or []:
                if getattr(item, "end_date", 0) > time.time():
                    auctions.append(item)
            for s in getattr(res, "sets", []):
                if getattr(s, "is_auction", False) and getattr(s, "end_date", 0) > time.time():
                    auctions.append(s)
            return auctions
        except Exception as e:
            logger.error(f"⚠️ Ошибка получения аукционов: {e}")
            return []

    async def buy_gift(self, gift_id: int, name: str) -> bool:
        try:
            await asyncio.sleep(self.config.get("buy_delay_seconds", 3.0))
            await self.client(functions.messages.SendGiftRequest(
                to_peer=types.InputUserSelf(),
                gift=types.InputGift(id=gift_id),
                message="Auto-purchased [Gift Sniper]"
            ))
            self.purchased.add(gift_id)
            await self.notifier.send("✅ Успешная покупка", f"#{gift_id} ({name}) куплен", "info")
            return True
        except FloodWaitError as e:
            logger.warning(f"⏳ FloodWait: {e.seconds}с")
            await asyncio.sleep(e.seconds + 2)
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка покупки #{gift_id}: {e}")
            await self.notifier.send("❌ Ошибка покупки", f"#{gift_id}: {str(e)}", "error")
            return False

    async def place_bid(self, gift_id: int, amount: int) -> bool:
        try:
            await self.client.invoke(functions.messages.BidGiftAuctionRequest(
                gift_id=gift_id, bid_amount=amount, message="Auto-bid [Gift Sniper]"
            ))
            await self.notifier.send("🔨 Авто-ставка", f"#{gift_id}: {amount}⭐", "info")
            return True
        except FloodWaitError as e:
            logger.warning(f"⏳ FloodWait на ставку: {e.seconds}с")
            await asyncio.sleep(e.seconds + 2)
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка ставки #{gift_id}: {e}")
            return False

    async def handle_auction(self, auc: Any):
        gid = getattr(auc, "id", None)
        current = int(getattr(auc, "current_bid", 0))
        end_ts = int(getattr(auc, "end_date", 0))
        max_bid = int(self.config.get("auction_max_bid_stars", 50000))
        step = int(self.config.get("auction_bid_step", 100))
        snipe_win = int(self.config.get("auction_snipe_last_minutes", 5)) * 60
        dry = self.config.get("dry_run", True)

        if not gid or end_ts <= time.time() or current >= max_bid:
            return
        if (end_ts - time.time()) > snipe_win:
            return

        next_bid = current + step
        if next_bid > max_bid: return

        logger.info(f"🔨 Аукцион #{gid}: {current}⭐ → {next_bid}⭐")
        if dry:
            logger.info("🧪 DRY-RUN: ставка пропущена")
            return

        await self.place_bid(gid, next_bid)
        await asyncio.sleep(max(6, step // 10))

    async def monitor(self):
        self.running = True
        logger.info("🔍 Мониторинг запущен (collectible + auctions + ultra-rare)")

        while self.running:
            self.reload_config()
            dry = self.config.get("dry_run", True)
            try:
                gifts = await self.fetch_gifts()
                for g in gifts:
                    if not self.is_collectible(g): continue
                    await self.check_ultra_rare(g)
                    if dry: continue
                    gid = getattr(g, "id", None)
                    price = getattr(g, "price", 0)
                    mn, mx = self.config.get("min_price_stars", 0), self.config.get("max_price_stars", 50000)
                    if gid and gid not in self.purchased and mn <= price <= mx:
                        if await self.buy_gift(gid, getattr(g, "name", "?")):
                            self.purchased.add(gid)

                if self.config.get("auto_bid_auctions", False):
                    auctions = await self.fetch_auctions()
                    for a in auctions:
                        await self.handle_auction(a)
            except Exception as e:
                logger.error(f"❌ Ошибка цикла: {e}")
            await asyncio.sleep(4)

    def stop(self):
        self.running = False
