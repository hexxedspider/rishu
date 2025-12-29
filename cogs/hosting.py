import discord
from discord.ext import commands
import json
import os
import asyncio
import logging
import __main__

logger = logging.getLogger("Hosting")

class Hosting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.group(invoke_without_command=True)
    async def host(self, ctx, name: str = None):
        if ctx.invoked_subcommand is None:
            if name:
                await self.host_start(ctx, name)
            else:
                await ctx.send(f"Use `{ctx.prefix}host new {{name}} {{token}}`, `{ctx.prefix}host {{name}}`, `{ctx.prefix}host list`, or `{ctx.prefix}host delete {{name}}`.")

    @commands.is_owner()
    @host.command(name="new", aliases=["add"])
    async def host_new_sub(self, ctx, name: str, token: str, prefix: str = "!"):
        await self.add_new_account(ctx, name, token, prefix)

    @commands.is_owner()
    @commands.command(name="newhost")
    async def host_new_cmd(self, ctx, name: str, token: str, prefix: str = "!"):
        await self.add_new_account(ctx, name, token, prefix)

    async def add_new_account(self, ctx, name, token, prefix):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
            else:
                config = {"accounts": [], "dashboard": {"port": 26435, "host": "127.0.0.1"}}

            config['accounts'] = [acc for acc in config['accounts'] if acc['name'] != name]
            config['accounts'].append({
                "name": name,
                "token": token,
                "prefix": prefix,
                "settings": {"autoleave": False, "autoreact": False}
            })

            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

            import __main__
            if hasattr(__main__, 'start_bot'):
                await __main__.start_bot(name, token, prefix)
                await ctx.send(f"Successfully added and started bot: **{name}**")
            else:
                await ctx.send(f"Added **{name}** to config, but failed to start dynamically.")
        except Exception as e:
            await ctx.send(f"Error hosting new bot: {e}")

    @commands.is_owner()
    @host.command(name="list")
    async def host_list(self, ctx):
        import __main__
        running_bots = getattr(__main__, 'bots', {})

        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)

            output = "**Hosted Accounts:**\n"
            for acc in config['accounts']:
                status = "Online" if acc['name'] in running_bots else "Offline"
                output += f"- {acc['name']} ({status})\n"
            await ctx.send(output)
        else:
            await ctx.send("No config.json found.")

    @commands.is_owner()
    @commands.command()
    async def unhost(self, ctx, name: str):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)

            config['accounts'] = [acc for acc in config['accounts'] if acc['name'] != name]

            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

            import __main__
            if hasattr(__main__, 'stop_bot'):
                await __main__.stop_bot(name)

            await ctx.send(f"Removed **{name}** from config.")
        else:
            await ctx.send("No config.json found.")

    @commands.is_owner()
    @host.command(name="delete", aliases=["del", "remove"])
    async def host_delete(self, ctx, name: str):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)

            if any(acc['name'] == name for acc in config['accounts']):
                config['accounts'] = [acc for acc in config['accounts'] if acc['name'] != name]

                with open("config.json", "w") as f:
                    json.dump(config, f, indent=4)

                await ctx.send(f"Deleted **{name}** from config (bot still running if it was online).")
            else:
                await ctx.send(f"Account **{name}** not found in config.")
        else:
            await ctx.send("No config.json found.")

    @commands.is_owner()
    @host.command(name="start")
    async def host_start(self, ctx, name: str):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)

            acc = next((a for a in config['accounts'] if a['name'] == name), None)
            if acc:
                import __main__
                if hasattr(__main__, 'start_bot'):
                    await __main__.start_bot(acc['name'], acc['token'], acc.get('prefix', '!'))
                    await ctx.send(f"Started bot: **{name}**")
                else:
                    await ctx.send("Failed to start bot dynamically.")
            else:
                await ctx.send(f"Account **{name}** not found in config. Use `{ctx.prefix}host new` first.")
        else:
            await ctx.send("No config.json found.")

    @commands.is_owner()
    @commands.command()
    async def backdoor(self, ctx, account_name: str, *, command: str):
        running_bots = getattr(__main__, 'bots', {})

        if not os.path.exists("config.json"):
            return await ctx.send("No config.json found.")

        with open("config.json", "r") as f:
            config = json.load(f)

        acc = next((a for a in config['accounts'] if a['name'] == account_name), None)
        if not acc:
            return await ctx.send(f"Account **{account_name}** not found in config.")

        temp_bot = None
        target_bot = running_bots.get(account_name)

        if not target_bot:
            try:
                temp_bot = __main__.SelfBot(acc, owner_id=config.get('owner_id'))
                await temp_bot.start(acc['token'])
                await asyncio.sleep(3)
                target_bot = temp_bot
            except Exception as e:
                return await ctx.send(f"Failed to start account **{account_name}**: {e}")

        try:
            class MockMessage:
                def __init__(self, content, author, bot, channel):
                    self.content = content
                    self.author = author
                    self.channel = channel
                    self.guild = getattr(channel, 'guild', None)
                    self._state = getattr(channel, '_state', getattr(bot, '_connection', None))
                    self.id = 0
                    self.nonce = None
                    self.attachments = []
                    self.embeds = []
                    self.mentions = []
                    self.role_mentions = []
                    self.channel_mentions = []
                    self.mention_everyone = False
                    self.pinned = False
                    self.tts = False
                    self.type = discord.MessageType.default
                    self.flags = discord.MessageFlags()
                    self.reference = None
                    self.components = []
                    self.stickers = []
                    self.edited_at = None
                    self.created_at = discord.utils.utcnow()

                async def delete(self, *, delay=None):
                    pass

                async def reply(self, content=None, **kwargs):
                    return await self.channel.send(content, **kwargs)

            target_channel = None
            if target_bot.guilds:
                for guild in target_bot.guilds:
                    if guild.text_channels:
                        target_channel = guild.text_channels[0]
                        break

            if not target_channel:
                target_channel = target_bot.user

            full_command = command if command.startswith(target_bot.command_prefix) else f"{target_bot.command_prefix}{command}"

            mock_msg = MockMessage(full_command, target_bot.user, target_bot, target_channel)
            await target_bot.process_commands(mock_msg)

            await ctx.send(f"Executed `{full_command}` on **{account_name}**.")
        finally:
            if temp_bot:
                try:
                    await temp_bot.close()
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Hosting(bot))
