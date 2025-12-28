import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import os
from datetime import datetime
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class Vanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sniping = False
        self.checking = False
        self.claimed = False
        self.lock = threading.Lock()
        self.executor = None
        self.stop_event = threading.Event()

        vanity_settings = self.bot.account_config.get('settings', {}).get('vanity', {})
        self.vanities = vanity_settings.get('vanities', [])
        self.webhook = vanity_settings.get('webhook', {})
        self.token = vanity_settings.get('token', '')
        self.guild_id = vanity_settings.get('guild_id', '')
        self.threads = vanity_settings.get('threads', 2)

    def save_vanity_settings(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
            for acc in config['accounts']:
                if acc['name'] == self.bot.name:
                    if 'settings' not in acc:
                        acc['settings'] = {}
                    acc['settings']['vanity'] = {
                        'vanities': self.vanities,
                        'webhook': self.webhook,
                        'token': self.token,
                        'guild_id': self.guild_id,
                        'threads': self.threads
                    }
                    break
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

    def load_config(self):
        config_path = "Vanity/config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

    def load_vanities(self):
        vanities_path = "Vanity/vanity/vanities.txt"
        if os.path.exists(vanities_path):
            with open(vanities_path, "r") as f:
                return [line.strip() for line in f if line.strip()]
        return []

    async def send_webhook(self, vanity, message):
        webhook_url = self.webhook.get('url', '')
        if not webhook_url:
            return
        unix_ts = int(datetime.now().timestamp())
        data = {
            "content": "@everyone" if self.webhook.get("ping") else None,
            "embeds": [
                {
                    "description": f"> **{message}**\nVanity: `discord.gg/{vanity}`\nChecked: <t:{unix_ts}:R>",
                    "color": 5331320
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(webhook_url, json=data)
            except Exception as e:
                print(f"Failed to send webhook: {e}")

    @commands.is_owner()
    @commands.command()
    async def vanitysniper(self, ctx, action: str):
        if action.lower() == 'start':
            if self.sniping:
                await ctx.send("Vanity sniper is already running.")
                return
            if not self.token:
                await ctx.send("Vanity token not set up. Please set vanity settings in config.json")
                return
            if not self.vanities:
                await ctx.send("No vanities to snipe. Add them to vanity settings in config.json")
                return
            self.sniping = True
            self.claimed = False
            self.stop_event.clear()
            self.executor = ThreadPoolExecutor(max_workers=self.threads)
            await ctx.send("Starting vanity sniper...")
            asyncio.create_task(self.run_sniper())
        elif action.lower() == 'stop':
            if not self.sniping:
                await ctx.send("Vanity sniper is not running.")
                return
            self.sniping = False
            self.stop_event.set()
            if self.executor:
                self.executor.shutdown(wait=False)
            await ctx.send("Stopped vanity sniper.")
        else:
            await ctx.send("Usage: !vanitysniper start/stop")

    async def run_sniper(self):
        session = aiohttp.ClientSession()

        while self.sniping and not self.claimed:
            for vanity in self.vanities:
                if not self.sniping or self.claimed:
                    break

                try:
                    async with session.get(f"https://discord.com/api/v10/invites/{vanity}?with_counts=true") as resp:
                        if resp.status == 404:
                            await self.try_claim_vanity(vanity)
                except Exception as e:
                    print(f"Error checking {vanity}: {e}")
                await asyncio.sleep(1)

        await session.close()

    async def try_claim_vanity(self, vanity):
        try:
            headers = {
                "Authorization": self.token,
                "Content-Type": "application/json"
            }
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"https://discord.com/api/v9/guilds/{self.guild_id}/vanity-url",
                    headers=headers,
                    json={"code": vanity}
                ) as resp:
                    if resp.status == 200:
                        with self.lock:
                            if not self.claimed:
                                self.claimed = True
                                self.sniping = False
                                await self.bot.get_channel(self.bot.get_guild(int(self.guild_id)).system_channel.id or self.bot.user.dm_channel.id).send(f"Sniped vanity: discord.gg/{vanity}")
                                await self.send_webhook(vanity, "Sniped Vanity!")
        except Exception as e:
            print(f"Failed to claim {vanity}: {e}")

    @commands.is_owner()
    @commands.command()
    async def checkvanities(self, ctx):
        if self.checking:
            await ctx.send("Already checking vanities.")
            return
        if not self.vanities:
            await ctx.send("No vanities to check.")
            return
        self.checking = True
        await ctx.send("Checking vanities...")
        available = []
        taken = []
        async with aiohttp.ClientSession() as session:
            for vanity in self.vanities:
                try:
                    async with session.get(f"https://discord.com/api/v10/invites/{vanity}?with_counts=true") as resp:
                        if resp.status == 404:
                            available.append(vanity)
                        else:
                            taken.append(vanity)
                except Exception as e:
                    print(f"Error checking {vanity}: {e}")
                await asyncio.sleep(0.5)
        self.checking = False
        msg = f"Checked {len(self.vanities)} vanities.\nAvailable: {', '.join(available) if available else 'None'}\nTaken: {', '.join(taken) if taken else 'None'}"
        await ctx.send(msg)
        for vanity in available:
            await self.send_webhook(vanity, "Vanity Available!")

async def setup(bot):
    await bot.add_cog(Vanity(bot))
