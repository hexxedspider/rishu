import discord
from discord.ext import commands
import aiohttp
import asyncio
import io
import json
import os
from datetime import datetime

class Account(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.decor_cycle_task = None
        self.tags_cycle_task = None
        self.status_cycle_task = None
        self.hardcoded_presets = [
            (discord.Status.dnd, "placeholder"),
            (discord.Status.idle, "placeholder"),
            (discord.Status.online, "placeholder"),
            (discord.Status.dnd, "placeholder")
        ]

    @commands.command()
    async def setnickname(self, ctx, *, nickname: str = None):
        await ctx.guild.me.edit(nick=nickname)

    @commands.command()
    async def setstatus(self, ctx, status: str, *, text: str = None):
        status_map = {
            "online": discord.Status.online,
            "dnd": discord.Status.dnd,
            "idle": discord.Status.idle,
            "invisible": discord.Status.invisible,
        }
        discord_status = status_map.get(status.lower(), discord.Status.online)
        activity = discord.CustomActivity(name=text) if text else None
        await self.bot.change_presence(status=discord_status, activity=activity)
        print(f"Status updated to {status} with text: {text}")

    @commands.command()
    async def setbio(self, ctx, *, bio: str = ""):
        try:
            await self.bot.user.edit(bio=bio)
        except Exception as e:
            await ctx.send(f"Failed to set bio: {e}", delete_after=5)

    @commands.command()
    async def setavatar(self, ctx, url: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await ctx.send("Failed to download image.", delete_after=5)
                    data = await resp.read()
                    await self.bot.user.edit(avatar=data)
            except Exception as e:
                await ctx.send(f"Failed to set avatar: {e}", delete_after=5)

    @commands.command()
    async def setbanner(self, ctx, url: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await ctx.send("Failed to download image.", delete_after=5)
                    data = await resp.read()
                    await self.bot.user.edit(banner=data)
            except Exception as e:
                if "Profile banners" in str(e):
                    await ctx.send("Failed: Bot lacks Nitro (Banners are Nitro-only).", delete_after=5)
                else:
                    await ctx.send(f"Failed to set banner: {e}", delete_after=5)

    @commands.command()
    async def setpronouns(self, ctx, *, pronouns: str = ""):
        try:
            await self.bot.http.request(discord.http.Route('PATCH', '/users/@me/profile'), json={"pronouns": pronouns})
        except Exception as e:
            await ctx.send(f"Failed to set pronouns: {e}", delete_after=5)

    @commands.group(invoke_without_command=True)
    async def steal(self, ctx, user: discord.User, *args):
        await ctx.message.delete()
        clone = "-c" in args or "--clone" in args
        
        try:
            profile = await user.profile()
        except Exception as e:
            return await ctx.send(f"Failed to fetch profile: {e}", delete_after=5)

        details = [
            f"**--- Profile Info: {user} ---**",
            f"**ID:** `{user.id}`",
            f"**Bot:** `{user.bot}`",
            f"**Created:** `{user.created_at.strftime('%Y-%m-%d %H:%M:%S')}`",
            f"**Bio:** {profile.bio or 'None'}",
            f"**Pronouns:** {getattr(profile.metadata, 'pronouns', 'None')}",
            f"**Accent Color:** {profile.accent_color or 'None'}",
            f"**Banner URL:** {profile.banner.url if profile.banner else 'None'}",
            f"**Avatar URL:** {user.avatar.url if user.avatar else 'None'}"
        ]

# leave this in comments in case i or someone else wants to print to the console in the future 
# print(f"{details}")

        if profile.badges:
            badge_display = []
            for b in profile.badges:
                if b.name.startswith('boost_'):
                    tier = b.name.split('_')[1]
                    badge_display.append(f"{tier}m")
                elif 'Earned' not in b.description and 'Server boosting' not in b.description:
                    badge_display.append(b.description)
            if badge_display:
                details.append(f"**Badges:** {', '.join(badge_display)}")

        if ctx.guild:
            member = ctx.guild.get_member(user.id)
            if member:
                details.append(f"**Joined Guild:** `{member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}`")
                details.append(f"**Nickname:** `{member.nick or 'None'}`")
                roles = [role.name for role in member.roles if role.name != "@everyone"]
                details.append(f"**Roles:** {', '.join(roles) if roles else 'None'}")

        info_msg = "\n".join(details)
        print(f"[Steal] Info requested for {user}")

        if not clone:
            return

        print(f"[Steal] Cloning {user}...")
        backup_dir = f"backups/bot_{self.bot.user.id}"
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, "original_profile.json")

        if not os.path.exists(backup_file):
            print("[Steal] Creating first-time backup...")
            my_profile = await self.bot.user.profile()
            backup_data = {
                "bio": my_profile.bio,
                "pronouns": getattr(my_profile.metadata, 'pronouns', ""),
            }
            
            async with aiohttp.ClientSession() as session:
                if self.bot.user.avatar:
                    async with session.get(self.bot.user.avatar.url) as r:
                        if r.status == 200:
                            with open(os.path.join(backup_dir, "avatar.png"), "wb") as f:
                                f.write(await r.read())
                if my_profile.banner:
                    async with session.get(my_profile.banner.url) as r:
                        if r.status == 200:
                            with open(os.path.join(backup_dir, "banner.png"), "wb") as f:
                                f.write(await r.read())
            
            with open(backup_file, "w") as f:
                json.dump(backup_data, f, indent=4)
            print("[Steal] Backup saved.")

        status = {"Avatar": "no", "Bio": "no", "Banner": "no", "Pronouns": "no", "Nickname": "no"}
        edit_kwargs = {}
        
        async with aiohttp.ClientSession() as session:
            if user.avatar:
                try:
                    async with session.get(user.avatar.url) as resp:
                        if resp.status == 200:
                            edit_kwargs['avatar'] = await resp.read()
                            status["Avatar"] = "yes"
                except: pass

            edit_kwargs['bio'] = profile.bio or ""
            status["Bio"] = "yes"

            if profile.accent_color:
                edit_kwargs['accent_color'] = profile.accent_color.value
                status["Accent Color"] = "yes"
            else:
                status["Accent Color"] = "none"

            if profile.banner:
                try:
                    async with session.get(profile.banner.url) as resp:
                        if resp.status == 200:
                            edit_kwargs['banner'] = await resp.read()
                            status["Banner"] = "yes"
                except: pass

        if edit_kwargs:
            try:
                await self.bot.user.edit(**edit_kwargs)
            except Exception as e:
                if "Profile banners" in str(e):
                    status["Banner"] = "Nitro Required"
                    edit_kwargs.pop('banner', None)
                    if edit_kwargs:
                        try: await self.bot.user.edit(**edit_kwargs)
                        except: pass

        try:
            pronouns = getattr(profile.metadata, 'pronouns', None)
            if pronouns:
                await self.bot.http.request(discord.http.Route('PATCH', '/users/@me/profile'), json={"pronouns": pronouns})
                status["Pronouns"] = "yes"
            else:
                status["Pronouns"] = "none"
        except:
            status["Pronouns"] = "no"

        if ctx.guild:
            try:
                await ctx.guild.me.edit(nick=user.display_name or user.name)
                status["Nickname"] = "yes"
            except:
                status["Nickname"] = "no"

        summary = "\n".join([f"**{k}:** {v}" for k, v in status.items()])
        print(f"[Steal] Cloned {user}: {summary}")

    @commands.command()
    async def restore(self, ctx):
        await ctx.message.delete()
        backup_dir = f"backups/bot_{self.bot.user.id}"
        backup_file = os.path.join(backup_dir, "original_profile.json")

        if not os.path.exists(backup_file):
            return await ctx.send("No backup found!", delete_after=5)

        try:
            with open(backup_file, "r") as f:
                data = json.load(f)

            edit_kwargs = {
                "bio": data.get("bio", ""),
            }

            if os.path.exists(os.path.join(backup_dir, "avatar.png")):
                with open(os.path.join(backup_dir, "avatar.png"), "rb") as f:
                    edit_kwargs["avatar"] = f.read()

            if os.path.exists(os.path.join(backup_dir, "banner.png")):
                with open(os.path.join(backup_dir, "banner.png"), "rb") as f:
                    edit_kwargs["banner"] = f.read()

            await self.bot.user.edit(**edit_kwargs)

            pronouns = data.get("pronouns", "")
            await self.bot.http.request(discord.http.Route('PATCH', '/users/@me/profile'), json={"pronouns": pronouns})
        except Exception as e:
            await ctx.send(f"Restore failed: {e}", delete_after=10)

    @commands.command()
    async def clear(self, ctx, limit: int = 100):
        async for message in ctx.channel.history(limit=limit):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                    await asyncio.sleep(0.5)
                except:
                    continue

    @commands.command()
    async def vcjoin(self, ctx, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        if isinstance(channel, discord.VoiceChannel):
            await channel.connect()
        else:
            await ctx.send("Invalid Voice Channel ID.")

    @commands.command()
    async def cycle_decor(self, ctx, *decor_ids: str):
        if self.decor_cycle_task and not self.decor_cycle_task.done():
            self.decor_cycle_task.cancel()
            self.decor_cycle_task = None
            return await ctx.send("Stopped decoration cycling.")
        
        if not decor_ids:
            return await ctx.send("Please provide at least one decoration ID.")
        
        async def do_cycle():
            while True:
                for d_id in decor_ids:
                    try:
                        await self.bot.user.edit(avatar_decoration=d_id)
                    except: pass
                    await asyncio.sleep(10)
        
        self.decor_cycle_task = asyncio.create_task(do_cycle())
        await ctx.send(f"Now cycling through {len(decor_ids)} decorations.")

    @commands.command()
    async def cycle_status(self, ctx, *, presets: str = None):
        if self.status_cycle_task and not self.status_cycle_task.done():
            self.status_cycle_task.cancel()
            self.status_cycle_task = None
            return await ctx.send("Stopped status cycling.")
        
        status_presets = []
        if presets:
            for p in presets.split('|'):
                parts = p.strip().split(':', 1)
                status_str = parts[0].strip().lower()
                text = parts[1].strip() if len(parts) > 1 else None
                
                status_map = {
                    "online": discord.Status.online,
                    "dnd": discord.Status.dnd,
                    "idle": discord.Status.idle,
                    "invisible": discord.Status.invisible,
                }
                discord_status = status_map.get(status_str, discord.Status.online)
                status_presets.append((discord_status, text))
        else:
            status_presets = self.hardcoded_presets
            
        if not status_presets:
            return await ctx.send("Please provide presets or ensure hardcoded ones exist.")

        async def do_cycle():
            while True:
                for discord_status, text in status_presets:
                    try:
                        activity = discord.CustomActivity(name=text) if text else None
                        await self.bot.change_presence(status=discord_status, activity=activity)
                    except: pass
                    await asyncio.sleep(30)
        
        self.status_cycle_task = asyncio.create_task(do_cycle())
        await ctx.send(f"Now cycling through {len(status_presets)} {'custom' if presets else 'hardcoded'} statuses.")

    @commands.command()
    async def prefix(self, ctx, new_prefix: str):
        self.bot.command_prefix = new_prefix

        import json
        import os
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)

            for acc in config['accounts']:
                if acc['name'] == self.bot.name:
                    acc['prefix'] = new_prefix
                    break

            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

async def setup(bot):
    await bot.add_cog(Account(bot))
