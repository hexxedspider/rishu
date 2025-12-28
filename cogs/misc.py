import discord
from discord.ext import commands
import asyncio
import random
import aiohttp
import datetime
import json
import os

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.silenced_users = set()
        self.owo_farming = False
        self.farming_channel = None
        self.random_offset = 3600
        self.sell_delay = 5
        self.owo_bot_id = 408785106942164992

        owo_settings = self.bot.account_config.get('settings', {}).get('owo', {})
        self.daily_hour = owo_settings.get('daily_hour', 12)
        self.timezone_offset = owo_settings.get('timezone_offset', -5)
        self.items_to_sell = set(owo_settings.get('items_to_sell', []))

        misc_settings = self.bot.account_config.get('settings', {}).get('misc', {})
        self.auto_self_react = misc_settings.get('auto_self_react', False)
        self.auto_react_others = misc_settings.get('auto_react_others', False)
        self.auto_leave_gc = misc_settings.get('auto_leave_gc', False)
        self.auto_react_emoji = misc_settings.get('auto_react_emoji', '👍')
        self.silenced_users = set(misc_settings.get('silenced_users', []))
        self.afk = misc_settings.get('afk', False)
        self.afk_message = misc_settings.get('afk_message', 'I am currently AFK.')

    def save_owo_settings(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
            for acc in config['accounts']:
                if acc['name'] == self.bot.name:
                    if 'settings' not in acc:
                        acc['settings'] = {}
                    acc['settings']['owo'] = {
                        'daily_hour': self.daily_hour,
                        'timezone_offset': self.timezone_offset,
                        'items_to_sell': list(self.items_to_sell)
                    }
                    break
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

    def save_misc_settings(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
            for acc in config['accounts']:
                if acc['name'] == self.bot.name:
                    if 'settings' not in acc:
                        acc['settings'] = {}
                    acc['settings']['misc'] = {
                        'auto_self_react': self.auto_self_react,
                        'auto_react_others': self.auto_react_others,
                        'auto_leave_gc': self.auto_leave_gc,
                        'auto_react_emoji': self.auto_react_emoji,
                        'silenced_users': list(self.silenced_users),
                        'afk': self.afk,
                        'afk_message': self.afk_message
                    }
                    break
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

    @commands.command()
    async def gcremake(self, ctx):
        if not isinstance(ctx.channel, discord.GroupChannel):
            return await ctx.send("This command only works in Group Chats.")

        members = [m for m in ctx.channel.recipients if m != self.bot.user]

        if not members:
            return await ctx.send("No other members found in this group chat.")

        friends = [rel.user for rel in self.bot.relationships if rel.type == discord.RelationshipType.friend]
        friend_members = [m for m in members if m in friends]

        if not friend_members:
            return await ctx.send("No friends found in this group chat to recreate with.")

        for recipient in members:
            try:
                await ctx.channel.remove_recipients(recipient)
                await asyncio.sleep(0.5)
            except: continue

        try:
            new_gc = await self.bot.create_group(*friend_members)
            await ctx.channel.leave()
        except discord.HTTPException as e:
            if e.status == 400 and e.code == 50007:
                await ctx.send("Failed to create group chat: Cannot send messages to one or more users. They may need to add the bot as a friend or enable DMs from server members.")
            else:
                await ctx.send(f"Failed to create group chat: {e}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def gcclap(self, ctx):
        if not isinstance(ctx.channel, discord.GroupChannel):
            return await ctx.send("This command only works in Group Chats.")
        
        for recipient in ctx.channel.recipients:
            if recipient != self.bot.user:
                try: 
                    await ctx.channel.remove_recipients(recipient)
                    await asyncio.sleep(0.5)
                except: continue

        await ctx.channel.leave()

    @commands.command()
    async def silence(self, ctx, user: discord.User):
        if user.id in self.silenced_users:
            self.silenced_users.remove(user.id)
        else:
            self.silenced_users.add(user.id)
        self.save_misc_settings()

    @commands.command() #untested, you can guess why, although given trying to make this work, im almost certain this wont, but no point in not trying
    async def spamreport(self, ctx, guild_id: int, channel_id: int, message_id: int, reason: int = 2):
        """Reports a message. Reason codes: 0: Illegal, 1: Harassment, 2: Spam, 3: Self-harm, 4: NSFW."""
        url = 'https://discordapp.com/api/v8/report'
        payload = {
            'channel_id': str(channel_id),
            'message_id': str(message_id),
            'guild_id': str(guild_id),
            'reason': reason
        }
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'sv-SE',
            'User-Agent': 'Discord/21295 CFNetwork/1128.0.1 Darwin/19.6.0',
            'Content-Type': 'application/json',
            'Authorization': self.bot.http.token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 201:
                    await ctx.send("[!] Reported successfully.")
                else:
                    try:
                        data = await resp.json()
                        msg = data.get('message', await resp.text())
                    except:
                        msg = await resp.text()
                    await ctx.send(f"[!] Error: {msg} | Status Code: {resp.status}")

    @commands.command()
    async def owomanager(self, ctx, action: str):
        if action.lower() == 'on':
            if self.owo_farming:
                return await ctx.send("OwO farming is already on.")
            self.owo_farming = True
            self.farming_channel = ctx.channel
            await ctx.send("OwO farming started.")
            self.bot.loop.create_task(self.owo_farming_loop())
            self.bot.loop.create_task(self.owo_daily_loop())
        elif action.lower() == 'off':
            if not self.owo_farming:
                return await ctx.send("OwO farming is already off.")
            self.owo_farming = False
            await ctx.send("OwO farming stopped.")
        else:
            await ctx.send("Usage: !owomanager on/off")

    @commands.command()
    async def setdaily(self, ctx, hour: int, offset: int):
        self.daily_hour = hour
        self.timezone_offset = offset
        self.save_owo_settings()

    @commands.command()
    async def sellrarity(self, ctx, action: str, rarity: str = None):
        if action.lower() == 'list':
            if self.items_to_sell:
                await ctx.send(f"Auto-sell rarities: {', '.join(self.items_to_sell)}")
            else:
                await ctx.send("No rarities set for auto-sell.")
        elif action.lower() in ['add', 'remove'] and rarity:
            rarity = rarity.lower()
            if action.lower() == 'add':
                self.items_to_sell.add(rarity)
                self.save_owo_settings()
            else:
                self.items_to_sell.discard(rarity)
                self.save_owo_settings()
        else:
            await ctx.send("Usage: !sellrarity add/remove <rarity> or !sellrarity list")

    @commands.command()
    async def autoreactself(self, ctx):
        self.auto_self_react = not self.auto_self_react
        self.save_misc_settings()

    @commands.command()
    async def autoreactothers(self, ctx, emoji: str = None):
        if emoji:
            self.auto_react_emoji = emoji
        self.auto_react_others = not self.auto_react_others
        self.save_misc_settings()

    @commands.command()
    async def autoleavegc(self, ctx):
        self.auto_leave_gc = not self.auto_leave_gc
        self.save_misc_settings()
        if self.auto_leave_gc:
            # Leave all current GCs
            for channel in self.bot.private_channels:
                if isinstance(channel, discord.GroupChannel):
                    try:
                        await channel.leave()
                    except:
                        pass

    @commands.command()
    async def afk(self, ctx, *, message: str = None):
        if message:
            if message.lower() == 'off':
                self.afk = False
            else:
                self.afk = True
                self.afk_message = message
        else:
            self.afk = not self.afk
        self.save_misc_settings()

    @commands.command()
    async def weather(self, ctx, *, city: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://wttr.in/{city}?format=3") as resp:
                if resp.status == 200:
                    data = await resp.text()
                    await ctx.send(f"Weather: {data}")
                else:
                    await ctx.send("Failed to get weather data.")

    @commands.command()
    async def define(self, ctx, word: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        definition = data[0]['meanings'][0]['definitions'][0]['definition']
                        await ctx.send(f"**{word}**: {definition}")
                    else:
                        await ctx.send("No definition found.")
                else:
                    await ctx.send("Failed to get definition.")

    async def owo_farming_loop(self):
        while self.owo_farming:
            if self.farming_channel:
                await self.farming_channel.send("owo hunt")
                await asyncio.sleep(random.randint(5, 15))
                await self.farming_channel.send("owo battle")
                await asyncio.sleep(random.randint(10, 30))
                await self.farming_channel.send("owo lb all")
                await asyncio.sleep(random.randint(5, 15))
                await self.farming_channel.send("owo crate all")
            delay = 3600 + random.randint(0, 3600)
            await asyncio.sleep(delay)

    async def owo_daily_loop(self):
        while self.owo_farming:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            local_tz = datetime.timezone(datetime.timedelta(hours=self.timezone_offset))
            now_local = now_utc.astimezone(local_tz)
            target_local = now_local.replace(hour=self.daily_hour, minute=0, second=0, microsecond=0)
            if now_local >= target_local:
                target_local += datetime.timedelta(days=1)
            offset_seconds = random.randint(-1800, 1800)
            target_local += datetime.timedelta(seconds=offset_seconds)
            target_utc = target_local.astimezone(datetime.timezone.utc)
            sleep_time = (target_utc - now_utc).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            if self.farming_channel and self.owo_farming:
                await self.farming_channel.send("owo daily")
            await asyncio.sleep(86400)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in self.silenced_users:
            try: await message.delete()
            except: pass

        if self.auto_self_react and message.author == self.bot.user:
            await message.add_reaction('⭐')

        if self.auto_react_others and message.author != self.bot.user and not message.author.bot:
            await message.add_reaction(self.auto_react_emoji)

        if self.afk and self.bot.user in message.mentions:
            await message.channel.send(self.afk_message)

        if isinstance(message.channel, discord.GroupChannel):
            pass

        if message.author.id == self.owo_bot_id and self.owo_farming and message.channel == self.farming_channel:
            content = message.content.lower()
            if 'you found' in content or 'obtained' in content or 'you opened' in content:
                items_to_sell = []
                rarities = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
                for r in rarities:
                    if r in content and r in self.items_to_sell:
                        items_to_sell.append(r)
                if items_to_sell:
                    await asyncio.sleep(self.sell_delay)
                    for item in items_to_sell:
                        await message.channel.send(f"owo sell {item} all")
                        await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(Misc(bot))
