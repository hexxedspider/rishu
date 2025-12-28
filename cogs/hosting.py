import discord
from discord.ext import commands
import json
import os
import asyncio
import logging

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
                await ctx.send(f"Use `{ctx.prefix}host new {{name}} {{token}}`, `{ctx.prefix}host {{name}}`, or `{ctx.prefix}host list`.")

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

async def setup(bot):
    await bot.add_cog(Hosting(bot))
