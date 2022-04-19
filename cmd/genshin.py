import datetime
import discord
import DiscordUtils
import cmd.asset.global_vars as Global
from cmd.asset.global_vars import defaultEmbed, setFooter
import yaml
from cmd.asset.classes import Character
from discord.ext import commands, tasks
from discord.ext.forms import Form

import genshin


with open(f'cmd/asset/accounts.yaml', encoding='utf-8') as file:
    users = yaml.full_load(file)


class GenshinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def getUserData(self, ctx, discordID: int):
        if discordID in users:
            cookies = {"ltuid": users[discordID]['ltuid'],
                       "ltoken": users[discordID]['ltoken']}
            uid = users[discordID]['uid']
            username = users[discordID]['name']
            return cookies, uid, username
        else:
            embed = Global.embedNoAccount
            setFooter(embed)
            await ctx.send(embed=embed)
            return

    @tasks.loop(hours=24)
    async def claimLoop():
        for user in users:
            userID = user
            cookies = {"ltuid": users[userID]['ltuid'],
                       "ltoken": users[userID]['ltoken']}
            uid = users[userID]['uid']
            client = genshin.Client(cookies)
            client.default_game = genshin.Game.GENSHIN
            client.lang = "zh-tw"
            client.uids[genshin.Game.GENSHIN] = uid
            try:
                await client.claim_daily_reward()
            except genshin.AlreadyClaimed:
                print(f"{users[userID]['name']} already claimed")
            else:
                print(f"claimed for {users[userID]['name']}")

    @tasks.loop(seconds=600)
    async def checkLoop(self):
        for user in users:
            userID = user
            try:
                cookies = {"ltuid": users[userID]['ltuid'],
                           "ltoken": users[userID]['ltoken']}
                uid = users[user]['uid']
                userObj = self.bot.get_user(userID)
                client = genshin.Client(cookies)
                client.default_game = genshin.Game.GENSHIN
                client.lang = "zh-tw"
                client.uids[genshin.Game.GENSHIN] = uid
                notes = await client.get_notes(uid)
                resin = notes.current_resin
                dateNow = datetime.datetime.now()
                diff = dateNow - users[userID]['dmDate']
                diffHour = diff.total_seconds() / 3600
                if resin >= 140 and users[userID]['dm'] == True and users[userID]['dmCount'] < 3 and diffHour >= 1:
                    time = notes.remaining_resin_recovery_time
                    hours, minutes = divmod(time // 60, 60)
                    fullTime = datetime.datetime.now() + datetime.timedelta(hours=hours)
                    printTime = '{:%H:%M}'.format(fullTime)
                    embed = defaultEmbed(f"<:danger:959469906225692703>: 目前樹脂數量已經超過140!",
                                         f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n於 {hours:.0f} 小時 {minutes:.0f} 分鐘後填滿(即{printTime})\n註: 不想收到這則通知打`!dm off`, 想重新打開打`!dm on`\n註: 部份指令, 例如`!check`可以在私訊運作")
                    setFooter(embed)
                    await userObj.send(embed=embed)
                    users[userID]['dmCount'] += 1
                    users[userID]['dmDate'] = dateNow
                    with open(f'cmd/asset/accounts.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
                elif resin < 140:
                    users[userID]['dmCount'] = 0
                    with open(f'cmd/asset/accounts.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(users, file)
            except genshin.errors.InvalidCookies:
                pass
            except AttributeError:
                print(f"{users[userID]['name']} 可能退群了")

    @checkLoop.before_loop
    async def beforeLoop(self):
        print('waiting...')
        await self.bot.wait_until_ready()

    @claimLoop.before_loop
    async def wait_until_1am():
        now = datetime.datetime.now().astimezone()
        next_run = now.replace(hour=1, minute=0, second=0)
        if next_run < now:
            next_run += datetime.timedelta(days=1)
        await discord.utils.sleep_until(next_run)

    checkLoop.start()
    claimLoop.start()

    @commands.command()
    async def check(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        memberID = member.id
        cookies, uid, username = await self.getUserData(ctx, memberID)
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        notes = await client.get_notes(uid)
        if not notes.expeditions:
            hr = 0
            mn = 0
            exTime = 0
        else:
            unfinExp = []
            for expedition in notes.expeditions:
                if(expedition.status == "Ongoing"):
                    unfinExp.append(expedition.remaining_time)
            if not unfinExp:
                hr = 0
                mn = 0
            else:
                exTime = min(unfinExp, default="EMPTY")
                hr, mn = divmod(exTime // 60, 60)
        time = notes.remaining_resin_recovery_time
        hours, minutes = divmod(time // 60, 60)
        fullTime = datetime.datetime.now() + datetime.timedelta(hours=hours)
        printTime = '{:%H:%M}'.format(fullTime)
        embedCheck = defaultEmbed(f"使用者: {username}", f"<:resin:956377956115157022> 目前樹脂: {notes.current_resin}/{notes.max_resin}\n於 {hours:.0f} 小時 {minutes:.0f} 分鐘後填滿(即{printTime})\n<:daily:956383830070140938> 已完成的每日數量: {notes.completed_commissions}/{notes.max_commissions}\n<:realm:956384011750613112> 目前塵歌壺幣數量: {notes.current_realm_currency}/{notes.max_realm_currency}\n<:expedition:956385168757780631> 已結束的探索派遣數量: {sum(expedition.finished for expedition in notes.expeditions)}/{len(notes.expeditions)}\n最快結束的派遣時間: {hr:.0f}小時 {mn:.0f}分鐘\n質變儀: {notes.transformer_recovery_time}")
        setFooter(embedCheck)
        await ctx.send(embed=embedCheck)

    @commands.command()
    async def stats(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        cookies, uid, username = await self.getUserData(ctx, member.id)
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        genshinUser = await client.get_partial_genshin_user(uid)
        days = genshinUser.stats.days_active
        char = genshinUser.stats.characters
        achieve = genshinUser.stats.achievements
        anemo = genshinUser.stats.anemoculi
        geo = genshinUser.stats.geoculi
        electro = genshinUser.stats.electroculi
        comChest = genshinUser.stats.common_chests
        exChest = genshinUser.stats.exquisite_chests
        luxChest = genshinUser.stats.luxurious_chests
        abyss = genshinUser.stats.spiral_abyss
        waypoint = genshinUser.stats.unlocked_waypoints
        embedStats = defaultEmbed(f"使用者: {username}",
                                  f":calendar: 活躍天數: {days}\n<:expedition:956385168757780631> 角色數量: {char}/48\n📜 成就數量:{achieve}/586\n🗺 已解鎖傳送錨點數量: {waypoint}\n🌙 深淵已達: {abyss}層\n<:anemo:956719995906322472> 風神瞳: {anemo}/66\n<:geo:956719995440730143> 岩神瞳: {geo}/131\n<:electro:956719996262821928> 雷神瞳: {electro}/181\n⭐ 一般寶箱: {comChest}\n🌟 稀有寶箱: {exChest}\n✨ 珍貴寶箱: {luxChest}")
        setFooter(embedStats)
        await ctx.send(embed=embedStats)

    @commands.command()
    async def area(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        cookies, uid, username = await self.getUserData(ctx, member.id)
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        genshinUser = await client.get_partial_genshin_user(uid)
        explorations = genshinUser.explorations
        exploreStr = ""
        offeringStr = ""
        for exploration in explorations:
            name = exploration.name
            percentage = exploration.explored
            offerings = exploration.offerings
            exploreStr += f"{name}: {percentage}%\n"
            for offering in offerings:
                offeringName = offering.name
                offeringLevel = offering.level
                offeringStr += f"{offeringName}: Lvl {offeringLevel}\n"
        embed = defaultEmbed(
            f"區域探索度: {username}", f"{exploreStr}\n{offeringStr}")
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def claim(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        cookies, uid, username = await self.getUserData(ctx, member.id)
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        reward = await client.claim_daily_reward()
        claimed_rewards = await client.get_reward_info()
        try:
            reward = await client.claim_daily_reward()
        except genshin.AlreadyClaimed:
            embed = defaultEmbed(
                f"使用者: {username}", f"❌ 已經拿過今天的每日獎勵啦! 貪心鬼{username}\n📘 這個月已領取的每日獎勵數量: {claimed_rewards}")
            setFooter(embed)
            await ctx.send(embed=embed)
        else:
            embed = defaultEmbed(
                f"使用者: {username}", f"✅ 幫你拿到了 {reward.amount}x {reward.name}\n📘 這個月已領取的每日獎勵數量: {claimed_rewards}")
            setFooter(embed)
            await ctx.send(embed=embed)

    @commands.command()
    async def abyss(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        cookies, uid, username = await self.getUserData(ctx, member.id)
        try:
            client = genshin.Client(cookies)
            client.lang = "zh-tw"
            client.default_game = genshin.Game.GENSHIN
            client.uids[genshin.Game.GENSHIN] = uid
            abyss = await client.get_spiral_abyss(uid)
            strongestStrike = abyss.ranks.strongest_strike
            mostKill = abyss.ranks.most_kills
            mostPlayed = abyss.ranks.most_played
            mostBurst = abyss.ranks.most_bursts_used
            mostSkill = abyss.ranks.most_skills_used
            mBurst = mostBurst[0].value
            mBurstChar = mostBurst[0].name
            mSkill = mostSkill[0].value
            mSkillChar = mostSkill[0].name
            mKill = mostKill[0].value
            mKillChar = mostKill[0].name
            mPlay = mostPlayed[0].value
            mPlayChar = mostPlayed[0].name
            dmg = strongestStrike[0].value
            dmgChar = strongestStrike[0].name
        except IndexError:
            embed = defaultEmbed(
                "找不到資料!", "可能是因為你還沒打深淵: 輸入`!stats`來看看你打到幾層\n也可能是資料還未更新: 再次輸入`!abyss`來確認")
            setFooter(embed)
            await ctx.send(embed=embed)
        embedAbyss = defaultEmbed(
            f"深境螺旋: {username}", f"💥 最高單次傷害角色: {dmgChar}, {dmg}點傷害\n☠ 擊殺王: {mKillChar}, {mKill}個擊殺\n🎄 最常使用角色: {mPlayChar}, {mPlay}次\n🇶 最多大招使用角色: {mBurstChar}, {mBurst}次\n🇪 最多小技能使用角色: {mSkillChar}, {mSkill}次")
        setFooter(embedAbyss)
        await ctx.send(embed=embedAbyss)

    @commands.command()
    async def diary(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        cookies, uid, username = await self.getUserData(ctx, member.id)
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        diary = await client.get_diary()
        primoCategoryStr = ""
        for category in diary.data.categories:
            primoCategoryStr += f"{category.percentage}%: {category.name} ({category.amount} 原石)" + "\n"
        embedDiary = defaultEmbed(
            f"原石與摩拉收入: {username}", f"<:mora:958577933650362468> **這個月獲得的摩拉數量: {diary.data.current_mora}**")
        embedDiary.add_field(
            name=f"<:primo:958555698596290570> 這個月獲得的原石數量: {diary.data.current_primogems}", value=f"收入分類: \n{primoCategoryStr}")
        setFooter(embedDiary)
        await ctx.send(embed=embedDiary)

    @commands.command()
    async def log(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        cookies, uid, username = await self.getUserData(ctx, member.id)
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        diary = await client.get_diary()
        primoLog = ""
        moraLog = ""
        async for action in client.diary_log(limit=25):
            primoLog = primoLog+f"{action.action} - {action.amount} 原石"+"\n"
        # async for action in client.diary_log(limit=25, type=genshin.models.DiaryType.MORA):
        #     moraLog = moraLog+f"{action.action} - {action.amount} 摩拉"+"\n"
        embedPrimo = defaultEmbed(
            f"<:primo:958555698596290570> 最近25筆原石紀錄", f"{primoLog}")
        setFooter(embedPrimo)
        embedMora = defaultEmbed(
            f"<:mora:958577933650362468> 最近25筆摩拉紀錄", f"{moraLog}")
        setFooter(embedMora)
        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
            ctx, remove_reactions=True)
        paginator.add_reaction('◀', "back")
        paginator.add_reaction('▶', "next")
        embeds = [embedPrimo, embedMora]
        await paginator.run(embeds)

    @commands.command()
    async def char(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        cookies, uid, username = await self.getUserData(ctx, member.id)
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        char = await client.get_genshin_characters(uid)
        clientCharacters = []
        charEmbeds = []
        for character in char:
            weapon = character.weapon
            artifacts = character.artifacts
            artifactList = []
            artifactIconList = []
            for artifact in artifacts:
                artifactList.append(artifact.name)
                artifactIconList.append(artifact.icon)
            clientCharacters.append(Character(character.name, character.level, character.constellation, character.icon,
                                              character.friendship, weapon.name, weapon.refinement, weapon.level, artifactList, artifactIconList))
        for character in clientCharacters:
            artifactStr = ""
            for artifact in character.artifacts:
                artifactStr = artifactStr + "- " + artifact + "\n"
            embedChar = defaultEmbed(f"{character.name}: C{character.constellation} R{character.refinement}",
                                     f"Lvl {character.level}\n好感度 {character.friendship}\n武器 {character.weapon}, lvl{character.weaponLevel}\n{artifactStr}")
            embedChar.set_thumbnail(url=f"{character.iconUrl}")
            setFooter(embedChar)
            charEmbeds.append(embedChar)
        paginator = DiscordUtils.Pagination.CustomEmbedPaginator(
            ctx, remove_reactions=True)
        paginator.add_reaction('⏮️', "first")
        paginator.add_reaction('◀', "back")
        paginator.add_reaction('▶', "next")
        paginator.add_reaction('⏭️', "last")
        await paginator.run(charEmbeds)

    @commands.command()
    async def users(self, ctx):
        userStr = ""
        count = 1
        for user in users:
            userID = user
            userStr = userStr + \
                f"{count}. {users[userID]['name']} - {users[userID]['uid']}\n"
            count += 1
        embed = defaultEmbed("所有帳號", userStr)
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    async def today(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        cookies, uid, username = await self.getUserData(ctx, member.id)
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        client.uids[genshin.Game.GENSHIN] = uid
        diary = await client.get_diary()
        mora = diary.day_data.current_mora
        primo = diary.day_data.current_primogems
        embed = defaultEmbed(f"今日收入: {username}", f"\
			<:primo:958555698596290570> {primo}原石\n\
			<:mora:958577933650362468> {mora}摩拉\n\n\
			註: 米哈遊對此資料更新速度較慢, 請見諒")
        setFooter(embed)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_role("小雪團隊")
    async def newuser(self, ctx):
        form = Form(ctx, '新增帳號設定流程', cleanup=True)
        form.add_question('原神UID?', 'uid')
        form.add_question('用戶名?', 'name')
        form.add_question('discord ID?', 'discordID')
        form.add_question('ltuid?', 'ltuid')
        form.add_question('ltoken?', 'ltoken')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        dateNow = datetime.datetime.now()
        cookies = {"ltuid": result.ltuid, "ltoken": result.ltoken}
        uid = result.uid
        client = genshin.Client(cookies)
        client.lang = "zh-tw"
        client.default_game = genshin.Game.GENSHIN
        failed = False
        try:
            await client.get_notes(uid)
        except genshin.errors.InvalidCookies:
            failed = True
        if not failed:
            users[int(result.discordID)] = {'name': result.name, 'uid': int(
                result.uid), 'ltoken': result.ltoken, 'ltuid': int(result.ltuid), 'dm': True, 'dmCount': 0, 'dmDate': dateNow}
            with open(f'cmd/asset/accounts.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(users, file)
            await ctx.send(f"已新增該帳號")
        else:
            await ctx.send("帳號資料錯誤，請檢查是否有輸入錯誤")


def setup(bot):
    bot.add_cog(GenshinCog(bot))
