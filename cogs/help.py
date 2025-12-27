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
        help_msg += "`setavatar`, `setbanner`, `setnickname`, `setpronouns`, `setbio`, `setstatus`, `steal`, `restore`, `clear`, `vcjoin`, `cycle_decor`, `cycle_tags`, `cycle_status`, `prefix`\n\n"
        
        help_msg += "__**Nuke & Wizz**__\n"
        help_msg += "`nuke`, `wizz`, `softwizz`, `vcclap`, `kickbots`\n\n"
        
        help_msg += "__**Misc**__\n"
        help_msg += "`gcremake`, `gcclap`, `silence`, `spamreport`\n\n"
        
        help_msg += "__**Troll**__\n"
        help_msg += "`ip`, `ddos`, `nitrogen`, `iplookup`\n\n"

        help_msg += "__**Hosting**__\n"
        help_msg += "`newhost`, `host list`, `host start`, `unhost`\n\n"

        
        help_msg += "*To see command details, use the dashboard or read the walkthrough.*"
        
        await ctx.send(help_msg)

async def setup(bot):
    await bot.add_cog(Help(bot))