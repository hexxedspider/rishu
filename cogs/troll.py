import discord
from discord.ext import commands
import random
import aiohttp
import asyncio


class Troll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ip(self, ctx, user: discord.Member = None):
        target = user or ctx.author
        ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        await ctx.send(f"grabbing ip for {target.mention}...")
        await asyncio.sleep(2.723)
        await ctx.send(f"*ip that was found:* `{ip}`")

    @commands.command()
    async def ddos(self, ctx, target: str):
        msg = await ctx.send(f"ddosing {target}...")
        await asyncio.sleep(11.892)
        await msg.edit(content=f"ddosed {target}")

    @commands.command()
    async def nitrogen(self, ctx): 
        code = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=16))
        await ctx.send(f"https://discord.gift/{code}")

    @commands.command()
    async def iplookup(self, ctx, ip: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://ip-api.com/json/{ip}") as resp:
                data = await resp.json()
                if data['status'] == 'fail':
                    return await ctx.send("Invalid IP or lookup failed.")
                
                info = (
                    f"**IP:** {data.get('query')}\n"
                    f"**Country:** {data.get('country')}\n"
                    f"**City:** {data.get('city')}\n"
                    f"**ISP:** {data.get('isp')}\n"
                )
                await ctx.send(info)

async def setup(bot):
    await bot.add_cog(Troll(bot))