import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.command()
    async def help(self, ctx):
        help_msg = "**Rishu Self-Bot Help Menu**\n\n"
        
        help_msg += "__**Account**__\n"
        help_msg += "`setavatar <url>` - Sets avatar\n"
        help_msg += "`setbanner <url>` - Sets banner\n"
        help_msg += "`setnickname <name>` - Sets nickname\n"
        help_msg += "`setpronouns <pronouns>` - Sets pronouns\n"
        help_msg += "`setbio <bio>` - Sets bio\n"
        help_msg += "`setstatus <status>` - Sets status\n"
        help_msg += "`steal <user> <<--clone|-c>>` - Steals profile\n"
        help_msg += "`restore` - Restores profile\n"
        help_msg += "`clear [amount]` - Clears own messages\n"
        help_msg += "`vcjoin <channel>` - Joins VC\n"
        help_msg += "`cycle_decor` - Cycles decorations\n"
        help_msg += "`cycle_tags` - Cycles tags\n"
        help_msg += "`cycle_status` - Cycles status\n"
        help_msg += "`prefix <new_prefix>` - Sets prefix\n"
        help_msg += "`restart` - Restarts bot\n\n"
        
        help_msg += "__**Nuke & Wizz**__\n"
        help_msg += "`nuke` - Nukes server\n"
        help_msg += "`wizz` - Wizzes server\n"
        help_msg += "`softwizz` - Soft wizzes server\n"
        help_msg += "`vcclap` - VC claps\n"
        help_msg += "`kickbots` - Kicks bots\n\n"

        help_msg += "__**Vanity (Owner Only)**__\n"
        help_msg += "`vanitysniper <start|stop>` - Start/stop vanity sniper\n"
        help_msg += "`checkvanities` - Check vanity availability\n\n"
        
        help_msg += "__**Misc**__\n"
        help_msg += "`gcremake` - Recreates group chat\n"
        help_msg += "`gcclap` - Leaves group chat\n"
        help_msg += "`silence <user>` - Silences user\n"
        help_msg += "`report <guild_id> <channel_id> <message_id>` - Reports message\n"
        help_msg += "`owomanager <on|off>` - Toggles OwO farming\n"
        help_msg += "`setdaily <hour> <offset>` - Sets daily time & timezone\n"
        help_msg += "`sellrarity <add|remove|list> [[rarity]]` - Manages auto-sell items\n"
        help_msg += "`autoreactself <emoji>` - Sets auto react emoji for self\n"
        help_msg += "`autoreactothers <emoji>` - Sets auto react emoji\n"
        help_msg += "`autoleavegc` - Toggles auto leave GCs\n"
        help_msg += "`afk <message>` - Sets AFK with message\n"
        help_msg += "`weather <city>` - Gets weather\n"
        help_msg += "`define <word>` - Defines word\n"
        help_msg += "`react <emoji> [user]` - Reacts to last message\n\n"
        
        help_msg += "__**Troll**__\n"
        help_msg += "`ip <<@person>>` - Grabs IP\n"
        help_msg += "`ddos <ip>` - DDoS simulation\n"
        help_msg += "`nitrogen` - Generates nitro\n"
        help_msg += "`iplookup <ip>` - IP lookup\n\n"

        help_msg += "__**owner cmds (Owner Only)**__\n"
        help_msg += "`newhost <name> <token>` - Adds new 3host\n"
        help_msg += "`host list` - Lists hosts\n"
        help_msg += "`host start <name>` - Starts host\n"
        help_msg += "`unhost <name>` - Removes host\n\n"
        
        help_msg += "*To see command details, use the dashboard or read the walkthrough.*"
        
        await ctx.send(help_msg, delete_after=20)

async def setup(bot):
    await bot.add_cog(Help(bot))
