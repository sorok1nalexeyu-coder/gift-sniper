import json
import os
from rich.console import Console
from rich.table import Table

console = Console()
CONFIG_PATH = os.path.join(os.getenv("DATA_DIR", "."), "config.json")

class ConfigManager:
    def __init__(self):
        self.config = self._load()

    def _load(self) -> dict:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return self._default_config()

    def _default_config(self) -> dict:
        return {
            "api_id": 0, "api_hash": "", "phone": "",
            "max_price_stars": 5000, "min_price_stars": 100,
            "buy_delay_seconds": 3.0,
            "only_collectibles": True,
            "allowed_rarities": ["collectible", "nft", "legendary", "epic"],
            "auto_bid_auctions": True,
            "auction_max_bid_stars": 25000,
            "auction_bid_step": 100,
            "auction_snipe_last_minutes": 5,
            "ultra_rare_threshold": 100,
            "ultra_rare_alert_channels": ["telegram", "webhook"],
            "dry_run": True,
            "notification_webhook": None,
            "notification_bot_token": "",
            "notification_chat_id": ""
        }

    def save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def display_gifts(self):
        table = Table(title="🎁 Текущие настройки фильтра")
        table.add_column("Параметр", style="cyan")
        table.add_column("Значение", style="green")
        for k, v in {
            "Только коллекционные": self.config.get("only_collectibles"),
            "Редкости": ", ".join(self.config.get("allowed_rarities", [])),
            "Мин/Макс цена": f"{self.config.get('min_price_stars')} - {self.config.get('max_price_stars')}⭐",
            "Dry-Run": self.config.get("dry_run"),
            "Ультра-редкий порог": f"≤{self.config.get('ultra_rare_threshold')} экз."
        }.items():
            table.add_row(k, str(v))
        console.print(table)
