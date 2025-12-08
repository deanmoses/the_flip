# Discord Posts via Bot

## Overview

Migrate outbound Discord notifications from webhooks to the Discord bot API. Currently, Flipfix posts events (problem reports, log entries, parts requests) to Discord via webhook URLs. This plan replaces that with Discord API calls using the bot token.

## Why Change

The current webhook system works, but we're adding a Discord bot for inbound message sync (see [DiscordBot.md](DiscordBot.md)). Consolidating to a single Discord integration provides:

1. **Single configuration** - One bot token instead of bot token + webhook URLs
2. **Single modality** - All Discord code uses the same API/library
3. **Richer interactions** - Buttons, threads, reactions on posted messages
4. **Dynamic user resolution** - Bot can resolve Discord usernames/avatars

## Current Architecture

```
Signal fires (e.g., ProblemReport created)
    ↓
dispatch_webhook() queues async task
    ↓
Django Q worker runs deliver_webhooks()
    ↓
_deliver_to_endpoint() formats message and POSTs to webhook URL
```

Key files:
- [signals.py](../../the_flip/apps/discord/signals.py) - Signal handlers that trigger webhooks
- [tasks.py](../../the_flip/apps/discord/tasks.py) - Async task queue logic
- [formatters.py](../../the_flip/apps/discord/formatters.py) - Build Discord embed payloads
- [models.py](../../the_flip/apps/discord/models.py) - `WebhookEndpoint`, `WebhookEventSubscription`

## New Architecture

```
Signal fires (e.g., ProblemReport created)
    ↓
dispatch_discord_post() queues async task    [same pattern]
    ↓
Django Q worker runs deliver_discord_post()  [same pattern]
    ↓
Post to Discord REST API using bot token     [swap HTTP POST target]
```

**We won't use the bot process to send messages**. Discord's REST API accepts bot token authentication for sending. The persistent WebSocket connection (the running bot) is only needed for *receiving* events like context menu commands.

This means:
- Django Q worker will post directly to Discord API (via the client lib we already have installed)
- We will not have inter-process communication between worker and bot
- We will reuse our existing retry/queue architecture

## Implementation Plan

### Phase 1: Add Bot-Based Posting (Parallel to Webhooks)

Create new posting mechanism without removing webhooks yet.

1. **Create `discord_api.py`** - Utility module for Discord REST API calls
   ```python
   import discord

   async def post_to_channel(channel_id: int, embeds: list[discord.Embed]) -> dict:
       """Post a message to a Discord channel using the bot token."""
       # Use discord.py's HTTP client or raw requests
       # Return success/error status
   ```

2. **Add new task** in `tasks.py`
   ```python
   def deliver_discord_post(event_type: str, object_id: int, model_name: str):
       """Deliver event to Discord via bot API (replaces webhook delivery)."""
       # Same logic as deliver_webhooks, but call post_to_channel instead
   ```

3. **Add configuration** (constance)
   - `DISCORD_POST_CHANNEL_ID` - Channel to post notifications to
   - `DISCORD_POSTS_VIA_BOT` - Toggle to switch from webhooks to bot (for gradual rollout)

4. **Update signals** to dispatch to new task when `DISCORD_POSTS_VIA_BOT` is enabled

### Phase 2: Feature Parity

Ensure bot posting matches webhook capabilities:

1. **Same embed formatting** - Reuse `formatters.py` (already builds embed dicts)
2. **Per-event-type toggles** - Reuse existing `DISCORD_WEBHOOKS_*` settings
3. **Error handling** - Same logging and error reporting

### Phase 3: Enhanced Features

Take advantage of bot capabilities:

1. **Buttons on posts** - "View in Flipfix", "Claim Issue"
2. **Thread creation** - Auto-create thread for discussion on problem reports
3. **Reactions** - Add emoji based on event type
4. **User mentions** - @mention maintainers when relevant

### Phase 4: Cleanup

Once bot posting is stable:

1. **Remove webhook models** - `WebhookEndpoint`, `WebhookEventSubscription`
2. **Remove webhook admin UI** - Endpoint management pages
3. **Remove webhook settings** - Constance config for webhooks
4. **Simplify signals** - Remove webhook dispatch code path

## Technical Decisions

### Keep Queue Architecture

We'll keep the queue architecture for posting to Discord.  The Django Q queue provides:

- Non-blocking signal handlers (web requests stay fast)
- Automatic retries on failure
- Timeout handling
- Logging and monitoring

No reason to change this.

### Use discord.py Library

We already have `discord.py==2.4.0` installed for the bot. Use it for posting too:

- `discord.Embed` - Type-safe embed building
- `discord.http.HTTPClient` - REST API calls without full bot connection
- Consistent with bot code

### Single Channel

Start with one notification channel (configurable).

The webhook system supported multiple endpoints with different subscriptions, but we don't need that.

## Configuration Changes

### Add
- `DISCORD_CHANNEL_ID` - Target channel for notifications

### Keep (Reuse)
- `DISCORD_BOT_TOKEN` - Already exists for bot
- `DISCORD_WEBHOOKS_PROBLEM_REPORTS` - Per-event toggles
- `DISCORD_WEBHOOKS_LOG_ENTRIES`
- `DISCORD_WEBHOOKS_PARTS`

### Remove (Phase 4)
- `WebhookEndpoint` model and admin
- `WebhookEventSubscription` model and admin

## Open Questions

- [ ] Should we support multiple channels (like webhook endpoints)?
- [ ] What buttons/interactions should we add to posted messages?
- [ ] Should problem reports auto-create a thread for discussion?
