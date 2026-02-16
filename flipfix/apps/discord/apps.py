from django.apps import AppConfig


class DiscordConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "flipfix.apps.discord"

    def ready(self):
        from flipfix.apps.discord.bot_handlers import discover as discover_bot_handlers
        from flipfix.apps.discord.webhook_handlers import (
            connect_signals,
        )
        from flipfix.apps.discord.webhook_handlers import (
            discover as discover_webhook_handlers,
        )

        discover_bot_handlers()
        discover_webhook_handlers()

        connect_signals()
