import discord
from discord.ext import commands
import asyncio
import random
import aiohttp

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.silenced_users = set()
        self.owo_farming = False

    @commands.command()
    async def gcremake(self, ctx):
        if not isinstance(ctx.channel, discord.GroupChannel):
            return await ctx.send("This command only works in Group Chats.")
        
        members = [m for m in ctx.channel.recipients if m != self.bot.user]
        
        for recipient in ctx.channel.recipients:
            if recipient != self.bot.user:
                try: 
                    await ctx.channel.remove_recipients(recipient)
                    await asyncio.sleep(0.5)
                except: continue
        
        if not members:
            return await ctx.send("No other members found in this group chat.")
        
        try:
            new_gc = await self.bot.create_group(*members)
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
            await ctx.send(f"Unsilenced {user}.")
        else:
            self.silenced_users.add(user.id)
            await ctx.send(f"Silenced {user}.")

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in self.silenced_users:
            try: await message.delete()
            except: pass

        if isinstance(message.channel, discord.GroupChannel):
            pass

async def setup(bot):
    await bot.add_cog(Misc(bot))
