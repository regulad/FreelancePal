"""
Regulad's docker-discord-template
https://github.com/regulad/docker-discord-template
"""

import asyncio
import datetime
import logging
import math
import os
from typing import Optional

import aiohttp
import discord
import dislog
from discord.ext import commands

remove_zero_padding_string: str = "#" if os.name == 'nt' else "-"


# Why is this different per-os? Seems like an overseight

class TimeCog(commands.Cog):
    """A set of tools for working with time."""

    @commands.command()
    async def timestamp(self, ctx: commands.Context) -> None:
        """Sends the current time as a Discord timestamp, and as plain text."""
        current_time: datetime.datetime = datetime.datetime.now()
        await ctx.send(f"The time is "
                       f"<t:{math.floor(current_time.timestamp())}:t> in your current timezone, "
                       f"which is {current_time.strftime(f'%{remove_zero_padding_string}I:%M %p')} "
                       f"in {current_time.astimezone().tzinfo.tzname(current_time)}, our native timezone.",
                       return_message=False)


class PayPalCog(commands.Cog):
    """A set of tools for working with PayPal invoices."""

    def __init__(self, paypal_client_id: str, paypal_secret: str, required_role: int, paypal_url: str) -> None:
        self._paypal_client: Optional[aiohttp.ClientSession] = None
        self._token_client: Optional[aiohttp.ClientSession] = None
        self._token_type: Optional[str] = None
        self._token: Optional[str] = None
        self._expiry: Optional[datetime.datetime] = None

        self._paypal_client_id: str = paypal_client_id
        self._paypal_secret: str = paypal_secret
        self._required_role: int = required_role
        self._paypal_url: str = paypal_url

    async def refresh_token(self) -> None:
        if self._token_client is None:
            self._token_client = aiohttp.ClientSession(
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en_US",
                },
                auth=aiohttp.BasicAuth(self._paypal_client_id, self._paypal_secret)
            )
        async with self._token_client.post(f"{self._paypal_url}/v1/oauth2/token",
                                           data="grant_type=client_credentials") as request:
            return_json: dict = await request.json()
            self._expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=return_json["expires_in"])
            self._token_type = return_json["token_type"]
            self._token = return_json["access_token"]

    async def cog_check(self, ctx: commands.Context) -> bool:
        role: discord.Role = ctx.guild.get_role(self._required_role)

        permissible: bool = role in ctx.author.roles

        if permissible:
            return permissible
        else:
            raise commands.MissingPermissions

    def cog_unload(self) -> None:
        if self._token_client is not None:
            asyncio.run_coroutine_threadsafe(self._token_client.close())
        if self._paypal_client is not None:
            asyncio.run_coroutine_threadsafe(self._paypal_client.close())

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        if self._expiry is None or datetime.datetime.utcnow() > self._expiry:
            await self.refresh_token()
        if self._paypal_client is None:
            self._paypal_client = aiohttp.ClientSession()

    @commands.command()
    async def invoice(
            self,
            ctx: commands.Context,
            amount: int = commands.Option(description="The amount of money, USD, that is owed."),
    ) -> None:
        """Creates an invoice for the specified amount and sends it."""
        await ctx.defer(ephemeral=True)
        await ctx.send("This command is not yet implemented.", ephemeral=True)


if __name__ == "__main__":
    debug: bool = os.environ.get("DEBUG") is not None

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    )

    if os.environ.get("LOGGING_WEBHOOK") is not None:
        logging.root.addHandler(dislog.DiscordWebhookHandler(os.environ.get("LOGGING_WEBHOOK")))

    # Initialize everything

    role_id: int = int(os.environ["FREELANCE_ROLE"])
    guild_id: int = int(os.environ["MAIN_GUILD"])

    bot: commands.Bot = commands.Bot(
        max_messages=None,  # Slim this bitch RIGHT down! We are never using messages.
        command_prefix=".",  # We don't use this.
        description=None,
        intents=discord.Intents(guilds=True),
        slash_command_guilds=[guild_id] if debug else None,
        message_commands=False,
        slash_commands=True,
        help_command=None,
        activity=discord.Game("Serious business.")
    )

    bot.add_cog(TimeCog())  # No prereq's for this

    maybe_paypal_secret: Optional[str] = os.environ.get("PAYPAL_SECRET")
    maybe_paypal_client_id: Optional[str] = os.environ.get("PAYPAL_CLIENT_ID")

    if maybe_paypal_secret is not None and maybe_paypal_client_id is not None:
        bot.add_cog(
            PayPalCog(
                maybe_paypal_client_id,
                maybe_paypal_secret,
                role_id,
                "https://api-m.paypal.com" if not debug else "https://api-m.sandbox.paypal.com"),
        )

    # Get running!

    bot.run(os.environ["DISCORD_TOKEN"])
