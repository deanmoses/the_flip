"""Discord bot: Context menu + LLM architecture."""

from __future__ import annotations

import logging
import traceback

import discord
from constance import config
from discord import app_commands

from the_flip.apps.discord.llm import MessageContext, RecordSuggestion, analyze_messages

logger = logging.getLogger(__name__)

# Flipfix base URL
FLIPFIX_URL = "https://theflip.app"


class RecordConfirmationView(discord.ui.View):
    """View with checkboxes and confirm/cancel buttons."""

    def __init__(self, suggestions: list[RecordSuggestion], context_summary: str):
        super().__init__(timeout=300)  # 5 minute timeout
        self.suggestions = suggestions
        self.context_summary = context_summary

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle confirm button click."""
        try:
            # Phase 2: Just show success message with link to home page
            # Phase 3 will wire up actual record creation
            embed = discord.Embed(
                title="Records Created",
                description="The following records were created in Flipfix:",
                color=discord.Color.green(),
            )

            for suggestion in self.suggestions:
                if suggestion.selected:
                    record_type_display = suggestion.record_type.replace("_", " ").title()
                    embed.add_field(
                        name=f"{record_type_display} - {suggestion.machine_name}",
                        value=f"[View in Flipfix]({FLIPFIX_URL})",
                        inline=False,
                    )

            # Disable all buttons after confirmation
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True

            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            logger.exception("discord_confirm_error: %s", e)
            await _send_error_response(interaction, "Failed to confirm records.")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle cancel button click."""
        try:
            embed = discord.Embed(
                title="Cancelled",
                description="No records were created.",
                color=discord.Color.greyple(),
            )

            # Disable all buttons after cancellation
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True

            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            logger.exception("discord_cancel_error: %s", e)
            await _send_error_response(interaction, "Failed to cancel.")


class FlipfixBot(discord.Client):
    """Discord bot with context menu command for recording to Flipfix."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True

        super().__init__(intents=intents)

        # Command tree for app commands (slash commands, context menus)
        self.tree = app_commands.CommandTree(self)
        self.tree.on_error = self._on_tree_error

    async def _on_tree_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Global error handler for app commands."""
        # Unwrap the CommandInvokeError to get the original exception
        original = error.__cause__ if isinstance(error, app_commands.CommandInvokeError) else error

        logger.exception(
            "discord_command_error",
            extra={
                "command": interaction.command.name if interaction.command else "unknown",
                "error": str(original),
                "traceback": traceback.format_exc(),
            },
        )

        await _send_error_response(
            interaction,
            "Something went wrong. Please try again or contact support if the problem persists.",
        )

    async def setup_hook(self):
        """Called when the bot is starting up."""

        @self.tree.context_menu(name="Record to Flipfix")
        async def record_to_flipfix(interaction: discord.Interaction, message: discord.Message):
            await self._handle_record_command(interaction, message)

        # Sync commands with Discord
        await self.tree.sync()
        logger.info("discord_bot_commands_synced")

    async def on_ready(self):
        """Called when the bot has connected to Discord."""
        logger.info(
            "discord_bot_connected",
            extra={
                "user": str(self.user),
                "user_id": self.user.id if self.user else None,
            },
        )

    async def _handle_record_command(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        """Handle the 'Record to Flipfix' context menu command."""
        # MUST defer immediately - Discord only gives 3 seconds to respond
        await interaction.response.defer(ephemeral=True)

        try:
            # Gather context around the clicked message
            context = await self._gather_context(message)

            # Analyze with LLM
            suggestions = await analyze_messages(context)

            # Build the confirmation embed
            if suggestions:
                embed = discord.Embed(
                    title="Record to Flipfix",
                    description="Review the suggested records below:",
                    color=discord.Color.blue(),
                )

                embed.add_field(
                    name="Context",
                    value=f"Analyzed {len(context.messages)} messages.",
                    inline=False,
                )

                for suggestion in suggestions:
                    record_type_display = suggestion.record_type.replace("_", " ").title()
                    checkbox = "☑" if suggestion.selected else "☐"
                    embed.add_field(
                        name=f"{checkbox} {record_type_display} - {suggestion.machine_name}",
                        value=suggestion.description[:100] + "..."
                        if len(suggestion.description) > 100
                        else suggestion.description,
                        inline=False,
                    )

                view = RecordConfirmationView(
                    suggestions, f"Analyzed {len(context.messages)} messages."
                )
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="No Records Suggested",
                    description="No maintenance records were identified in these messages.",
                    color=discord.Color.light_grey(),
                )
                embed.add_field(
                    name="Context",
                    value=f"Analyzed {len(context.messages)} messages.",
                    inline=False,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("discord_handle_record_error: %s", e)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Error",
                    description="Failed to analyze messages. Please try again.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

    async def _gather_context(self, message: discord.Message) -> MessageContext:
        """Gather context around the clicked message."""
        messages = []
        flipfix_urls = []

        try:
            async for msg in message.channel.history(limit=10, around=message):
                messages.append(msg)

                for embed in msg.embeds:
                    if embed.url and "theflip.app" in embed.url:
                        flipfix_urls.append(embed.url)
        except discord.HTTPException as e:
            logger.warning(
                "discord_gather_context_failed",
                extra={"message_id": message.id, "error": str(e)},
            )

        messages.sort(key=lambda m: m.created_at)

        message_dicts = []
        for msg in messages:
            message_dicts.append(
                {
                    "author": msg.author.display_name,
                    "content": msg.content,
                    "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M"),
                    "is_target": msg.id == message.id,
                }
            )

        return MessageContext(
            messages=message_dicts,
            target_message_id=message.id,
            flipfix_urls=flipfix_urls,
        )


async def _send_error_response(interaction: discord.Interaction, message: str):
    """Send an error response, handling both deferred and non-deferred states."""
    embed = discord.Embed(
        title="Error",
        description=message,
        color=discord.Color.red(),
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException as e:
        # Interaction may have expired - just log it
        logger.warning("discord_error_response_failed: %s", e)


def run_bot():
    """Run the Discord bot. Called from the management command."""
    if not config.DISCORD_BOT_ENABLED:
        logger.error("Discord bot is disabled in settings")
        return

    token = config.DISCORD_BOT_TOKEN
    if not token:
        logger.error("Discord bot token not configured")
        return

    bot = FlipfixBot()

    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord bot token")
    except Exception as e:
        logger.exception("Discord bot error: %s", e)
