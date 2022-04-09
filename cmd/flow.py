import getpass
owner = getpass.getuser()
import sys 
sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')
import os, discord, asyncio, genshin, yaml, datetime
import global_vars
global_vars.Global()
from discord.ext import commands
from discord.ext.forms import Form

with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', encoding = 'utf-8') as file:
	users = yaml.full_load(file)

class FlowCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def flow(self, ctx, *, name: discord.Member = None):
		name = name or ctx.author.id
		found = False
		for user in users:
			if user['discordID']==name:
				found = True
				await ctx.send(f"使用者: {user['name']}\nflow幣: {user['flow']}")
		if found == False:
			discordID = name
			name = ctx.author
			newUser = {'name': str(name), 'discordID': int(discordID), 'flow': 0}
			users.append(newUser)
			with open(f'C:/Users/{owner}/shenhe_bot/asset/flow.yaml', 'w', encoding = 'utf-8') as file:
				yaml.dump(users, file)
			await ctx.send("你本來沒有帳號, 現在申鶴幫你做了一個, 再打`!flow`一次試試看")

	@commands.command()
	@commands.is_owner()
	async def roles(self, ctx):
		channel = self.bot.get_channel(962311051683192842)
		embed = global_vars.defaultEmbed("請選擇你的世界等級", " ")
		global_vars.setFooter(embed)
		message = await channel.send(embed=embed)
		await message.add_reaction('1️⃣')
		await message.add_reaction('2️⃣')
		await message.add_reaction('3️⃣')
		await message.add_reaction('4️⃣')
		await message.add_reaction('5️⃣')
		await message.add_reaction('6️⃣')
		await message.add_reaction('7️⃣')
		await message.add_reaction('8️⃣')

	@commands.command()
	async def find(self, ctx):
		
from discord.ext import commands
bot = commands.Bot(command_prefix="!")

@bot.command()
async def testform(ctx):
    form = Form(ctx,'Title')
    form.add_question('Question 1','first')
    form.add_question('Question 2','second')
    form.add_question('Question 3','third')
    result = await form.start()
    return result


def setup(bot):
	bot.add_cog(FlowCog(bot))