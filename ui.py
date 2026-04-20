from rich.prompt import Prompt, IntPrompt, Confirm
from rich.console import Console
from config_manager import ConfigManager

console = Console()

class SetupUI:
    def __init__(self, cfg_mgr: ConfigManager):
        self.cfg = cfg_mgr

    def run_setup(self):
        console.print("\n🎁 [bold cyan]Gift Sniper — Первичная настройка[/bold cyan]\n")
        c = self.cfg.config

        c["api_id"] = IntPrompt.ask("  api_id (my.telegram.org)", default=c["api_id"])
        c["api_hash"] = Prompt.ask("  api_hash", default=c["api_hash"])
        c["phone"] = Prompt.ask("  Телефон (+7...)", default=c["phone"])

        console.print("\n💰 [bold yellow]Фильтр подарков[/bold yellow]")
        c["only_collectibles"] = Confirm.ask("  Покупать ТОЛЬКО коллекционные?", default=True)
        c["min_price_stars"] = IntPrompt.ask("  Мин. цена (⭐)", default=c["min_price_stars"])
        c["max_price_stars"] = IntPrompt.ask("  Макс. цена (⭐)", default=c["max_price_stars"])

        console.print("\n🔨 [bold yellow]Аукционы[/bold yellow]")
        c["auto_bid_auctions"] = Confirm.ask("  Авто-ставки на аукционах?", default=True)
        c["auction_max_bid_stars"] = IntPrompt.ask("  Макс. ставка (⭐)", default=c["auction_max_bid_stars"])
        c["auction_bid_step"] = IntPrompt.ask("  Шаг ставки (⭐)", default=c["auction_bid_step"])

        console.print("\n🚨 [bold yellow]Ультра-редкие алерты[/bold yellow]")
        c["ultra_rare_threshold"] = IntPrompt.ask("  Порог тиража (≤X = алерт)", default=c["ultra_rare_threshold"])
        c["notification_bot_token"] = Prompt.ask("  Токен Telegram-бота (для уведомлений, опц.)", default=c["notification_bot_token"])
        c["notification_chat_id"] = Prompt.ask("  Chat ID для уведомлений (опц.)", default=c["notification_chat_id"])

        c["dry_run"] = Confirm.ask("  🔒 Включить DRY-RUN (без реальных покупок/ставок)?", default=True)
        
        self.cfg.save()
        self.cfg.display_gifts()
        console.print("\n[bold green]💾 Конфигурация сохранена в /data/config.json[/bold green]\n")
