import discord
from discord.ext import commands
import aiohttp
import asyncio
import io
import json
import os
import sys
import random
import shutil
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
        async def delete_command():
            await asyncio.sleep(10)
            try:
                await ctx.message.delete()
            except:
                pass

        asyncio.create_task(delete_command())

        status_map = {
            "online": discord.Status.online,
            "dnd": discord.Status.dnd,
            "idle": discord.Status.idle,
            "invisible": discord.Status.invisible,
        }
        discord_status = status_map.get(status.lower(), discord.Status.online)
        activity = discord.CustomActivity(name=text) if text else None
        await self.bot.change_presence(status=discord_status, activity=activity)

    @commands.command()
    async def setbio(self, ctx, *, bio: str = ""):
        async def delete_command():
            await asyncio.sleep(10)
            try:
                await ctx.message.delete()
            except:
                pass

        asyncio.create_task(delete_command())

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
        async def delete_command():
            await asyncio.sleep(10)
            try:
                await ctx.message.delete()
            except:
                pass
            
        asyncio.create_task(delete_command())
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

        if profile.badges:
            badge_display = []
            for b in profile.badges:
                if 'Server boosting' in b.description:
                    badge_display.append("Server Booster")
                elif 'Earned' not in b.description:
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
            try:
                await ctx.send(info_msg)
            except Exception as e:
                pass
            return

        backup_dir = f"backups/bot_{self.bot.user.id}"
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, "original_profile.json")

        if not os.path.exists(backup_file):
            try:
                my_profile = await self.bot.user.profile()
                backup_data = {
                    "bio": my_profile.bio or "",
                    "pronouns": getattr(my_profile.metadata, 'pronouns', "") or "",
                    "accent_color": my_profile.accent_color.value if my_profile.accent_color else None,
                }

                async with aiohttp.ClientSession() as session:
                    if self.bot.user.avatar:
                        try:
                            async with session.get(self.bot.user.avatar.url) as r:
                                if r.status == 200:
                                    with open(os.path.join(backup_dir, "avatar.png"), "wb") as f:
                                        f.write(await r.read())
                        except Exception as e:
                            pass
                    if my_profile.banner:
                        try:
                            async with session.get(my_profile.banner.url) as r:
                                if r.status == 200:
                                    with open(os.path.join(backup_dir, "banner.png"), "wb") as f:
                                        f.write(await r.read())
                        except Exception as e:
                            pass

                with open(backup_file, "w") as f:
                    json.dump(backup_data, f, indent=4)
            except Exception as e:
                return await ctx.send("Failed to create backup. Cannot proceed with cloning.", delete_after=10)

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
                print(f"[Steal] Successfully updated profile with: {list(edit_kwargs.keys())}")
            except Exception as e:
                if "Profile banners" in str(e):
                    status["Banner"] = "Nitro Required"
                    edit_kwargs.pop('banner', None)
                    if edit_kwargs:
                        try:
                            await self.bot.user.edit(**edit_kwargs)
                            print(f"[Steal] Successfully updated profile with: {list(edit_kwargs.keys())}")
                        except Exception as e2:
                            pass

        try:
            pronouns = getattr(profile.metadata, 'pronouns', None)
            if pronouns:
                await self.bot.http.request(discord.http.Route('PATCH', '/users/@me/profile'), json={"pronouns": pronouns})
                status["Pronouns"] = "yes"
            else:
                status["Pronouns"] = "none"
        except Exception as e:
            status["Pronouns"] = "no"

        if ctx.guild:
            try:
                await ctx.guild.me.edit(nick=user.display_name or user.name)
                status["Nickname"] = "yes"
            except Exception as e:
                status["Nickname"] = "no"

        try:
            verification_profile = await self.bot.user.profile()
            verification_status = {
                "Avatar": "OK" if self.bot.user.avatar and user.avatar else ("FAIL" if user.avatar else "N/A"),
                "Bio": "OK" if verification_profile.bio == (profile.bio or "") else "FAIL",
                "Banner": "OK" if self.bot.user.banner and profile.banner else ("Nitro" if not self.bot.user.banner and profile.banner else "N/A"),
                "Pronouns": "OK" if getattr(verification_profile.metadata, 'pronouns', None) == getattr(profile.metadata, 'pronouns', None) else "FAIL",
            }

            for key in verification_status:
                if key in status and verification_status[key] != "N/A":
                    status[key] = verification_status[key]

        except Exception as e:
            pass

    @commands.command()
    async def restore(self, ctx):
        async def delete_command():
            await asyncio.sleep(10)
            try:
                await ctx.message.delete()
            except:
                pass

        asyncio.create_task(delete_command())

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
            if pronouns:
                await self.bot.http.request(discord.http.Route('PATCH', '/users/@me/profile'), json={"pronouns": pronouns})

            await ctx.send("Profile restored successfully!", delete_after=5)

        except Exception as e:
            await ctx.send(f"Restore failed: {e}", delete_after=10)

    @commands.command()
    async def clear(self, ctx, limit: int = None):
        if limit is None:
            limit = 1000
        async for message in ctx.channel.history(limit=limit):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                    await asyncio.sleep(random.uniform(0.3, 1.0))
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
            return await ctx.send("Stopped decoration cycling.", delete_after=5)

        if not decor_ids:
            return await ctx.send("Please provide at least one decoration ID.", delete_after=5)

        async def do_cycle():
            while True:
                for d_id in decor_ids:
                    try:
                        await self.bot.user.edit(avatar_decoration=d_id)
                    except: pass
                    await asyncio.sleep(10)

        self.decor_cycle_task = asyncio.create_task(do_cycle())
        await ctx.send(f"Now cycling through {len(decor_ids)} decorations.", delete_after=5)

    @commands.command()
    async def cycle_status(self, ctx, action: str = "start"):
        if action.lower() == "stop":
            if self.status_cycle_task and not self.status_cycle_task.done():
                self.status_cycle_task.cancel()
                self.status_cycle_task = None
                return await ctx.send("Stopped status cycling.", delete_after=5)
            else:
                return await ctx.send("Status cycling is not running.", delete_after=5)

        if self.status_cycle_task and not self.status_cycle_task.done():
            return await ctx.send("Status cycling is already running. Use `cycle_status stop` to stop it first.", delete_after=5)

        status_config = {"presets": [], "cycle_delay": 30, "random_order": False}
        if os.path.exists("status.json"):
            try:
                with open("status.json", "r") as f:
                    status_config = json.load(f)
            except Exception as e:
                pass

        enabled_presets = [p for p in status_config.get("presets", []) if p.get("enabled", True)]

        if not enabled_presets:
            return await ctx.send("No enabled status presets found in status.json. Please check the file and enable some presets.", delete_after=5)

        status_map = {
            "online": discord.Status.online,
            "dnd": discord.Status.dnd,
            "idle": discord.Status.idle,
            "invisible": discord.Status.invisible,
        }

        status_presets = []
        for preset in enabled_presets:
            status_str = preset.get("status", "online").lower()
            text = preset.get("text", "")
            discord_status = status_map.get(status_str, discord.Status.online)
            status_presets.append((discord_status, text))

        cycle_delay = status_config.get("cycle_delay", 30)
        random_order = status_config.get("random_order", False)

        async def do_cycle():
            while True:
                current_presets = status_presets[:]
                if random_order:
                    random.shuffle(current_presets)

                for discord_status, text in current_presets:
                    try:
                        activity = discord.CustomActivity(name=text) if text else None
                        await self.bot.change_presence(status=discord_status, activity=activity)
                        print(f"[Cycle Status] Set to {discord_status} with text: {text}")
                    except Exception as e:
                        pass
                    await asyncio.sleep(cycle_delay)

        self.status_cycle_task = asyncio.create_task(do_cycle())
        await ctx.send(f"Now cycling through {len(status_presets)} status presets every {cycle_delay} seconds.", delete_after=5)

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

    @commands.command()
    async def restart(self, ctx):
        await ctx.send("Restarting bot...")
        await self.bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @commands.command()
    async def block(self, ctx, user: discord.User):
        try:
            await self.bot.http.request(
                discord.http.Route('PUT', '/users/@me/relationships/{user_id}', user_id=user.id),
                json={'type': 2}
            )
            await ctx.send(f"Blocked {user}.")
        except Exception as e:
            await ctx.send(f"Failed to block: {e}")

    @commands.command()
    async def unblock(self, ctx, user: discord.User):
        try:
            await self.bot.http.request(
                discord.http.Route('DELETE', '/users/@me/relationships/{user_id}', user_id=user.id)
            )
            await ctx.send(f"Unblocked {user}.")
        except Exception as e:
            await ctx.send(f"Failed to unblock: {e}")

    @commands.command()
    async def friend(self, ctx, user: discord.User):
        try:
            await self.bot.http.request(
                discord.http.Route('POST', '/users/@me/relationships'),
                json={'username': user.name, 'discriminator': user.discriminator or '0'}
            )
            await ctx.send(f"Sent friend request to {user}.")
        except Exception as e:
            await ctx.send(f"Failed to send friend request: {e}")

    @commands.command()
    async def unfriend(self, ctx, user: discord.User):
        try:
            await self.bot.http.request(
                discord.http.Route('DELETE', '/users/@me/relationships/{user_id}', user_id=user.id)
            )
            await ctx.send(f"Removed {user} from friends.")
        except Exception as e:
            await ctx.send(f"Failed to remove friend: {e}")

    @commands.command()
    async def join(self, ctx, invite: str):
        try:
            invite_code = invite.split('/')[-1] if '/' in invite else invite
            await self.bot.http.request(
                discord.http.Route('POST', '/invites/{invite_code}', invite_code=invite_code)
            )
            await ctx.send(f"Joined server via invite: {invite}")
        except Exception as e:
            await ctx.send(f"Failed to join: {e}")

    @commands.command()
    async def leave(self, ctx, guild_id: int = None):
        if guild_id:
            guild = self.bot.get_guild(guild_id)
        else:
            guild = ctx.guild

        if not guild:
            return await ctx.send("Guild not found.")

        try:
            await guild.leave()
            await ctx.send(f"Left {guild.name}.")
        except Exception as e:
            await ctx.send(f"Failed to leave: {e}")

    @commands.command()
    async def dump(self, ctx, guild_id: int = None):
        if guild_id:
            guild = self.bot.get_guild(guild_id)
        else:
            guild = ctx.guild

        if not guild:
            return await ctx.send("Guild not found.")

        info = f"**{guild.name}**\n"
        info += f"ID: {guild.id}\n"
        info += f"Owner: {guild.owner}\n"
        info += f"Members: {guild.member_count}\n"
        info += f"Channels: {len(guild.channels)}\n"
        info += f"Roles: {len(guild.roles)}\n"

        await ctx.send(info)

    @commands.command()
    async def friends(self, ctx):
        try:
            relationships = await self.bot.http.request(discord.http.Route('GET', '/users/@me/relationships'))
            friends = [rel for rel in relationships if rel['type'] == 1]
            if not friends:
                return await ctx.send("No friends found.")

            friend_list = "\n".join([f"- {rel['user']['username']}#{rel['user']['discriminator']}" for rel in friends[:20]])
            if len(friends) > 20:
                friend_list += f"\n... and {len(friends) - 20} more"
            await ctx.send(f"**Friends:**\n{friend_list}")
        except Exception as e:
            await ctx.send(f"Failed to get friends: {e}")

async def setup(bot):
    await bot.add_cog(Account(bot))
