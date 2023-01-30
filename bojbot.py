import discord
from discord.commands import Option
from discord.ext import tasks
import requests
import json
import time
import random as r

bot = discord.Bot()

rank_range = {"Unrated":[0], "Bronze":[1, 2, 3, 4, 5], "Silver":[6, 7, 8, 9, 10], 
              "Gold":[11, 12, 13, 14, 15], "Platinum":[16, 17, 18, 19, 20], 
              "Diamond":[21, 22, 23, 24, 25], "Ruby":[26, 27, 28, 29, 30]}

rank_name = {0:"Unrated", 1:"Bronze V", 2:"Bronze IV", 3:"Bronze III", 4:"Bronze II", 5:"Bronze I", 
             6:"Silver V", 7:"Silver IV", 8:"Silver III", 9:"Silver II", 10:"Silver I",
             11:"Gold V", 12:"Gold IV", 13:"Gold III", 14:"Gold II", 15:"Gold I",
             16:"Platinum V", 17:"Platinum IV", 18:"Platinum III", 19:"Platinum II", 20:"Platinum I",
             21:"Diamond V", 22:"Diamond IV", 23:"Diamond III", 24:"Diamond II", 25:"Diamond I",
             26:"Ruby V", 27:"Ruby IV", 28:"Ruby III", 29:"Ruby II" , 30:"Ruby I", 31:"Master"}

# value 값에 이모티콘 ID 넣기(String " ")
rank_imo = {"Bronze":0, "Silver":0, "Gold":0, 
           "Platinum":0, "Diamond":0, "Ruby":0, "Master":0,
           "admin":0, "baekjoon":0, "Bot":0}

# value 값에 역할 ID 넣기(integer)
role_id = {"Bronze":0, "Silver":0, "Gold":0, 
           "Platinum":0, "Diamond":0, "Ruby":0, "Master":0,
           "admin":0, "baekjoon":0, "Bot":0}

feers = 0.925
userList = []
DBid = {}
DBcoin = {}
idList = []
bytecoin = {}
bytebefore = {}
usercoin = {}

todaysProbID = -1
todaysProbRank = 0
min_LV = "b2"
max_LV = "g5"

#서버 / 채널 아이디 넣기(integer)
server_id = 0
channel_id = 0 # COIN 현황판 올라오는 채널
channel_TD = 0 # 랜덤 문제 올라오는 채널

boj = bot.create_group("boj")

def showproblem(id):
    url = "https://solved.ac/api/v3/problem/show"
    querystring = {"problemId":f"{id}"}
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    rtx = json.loads(response.text)
    title = rtx["titleKo"]
    lv = rank_name[int(rtx["level"])]
    algorithm = ""
    for tmp in rtx["tags"]:
        algorithm += "[" + tmp["displayNames"][0]["name"] + "] "
    algorithm = algorithm[:-1]
    embed = discord.Embed(title=f"{id}번 {title} [{lv}]", description=f"`{algorithm}`", url=f"https://www.acmicpc.net/problem/{id}",color=discord.Color.green())
    return embed

# get registered list 
# 디스코드 아이디 리스트 가져오기 (정렬 상태)
async def getIDList(ctx: discord.AutocompleteContext):
    return sorted([i for i in DBid.keys()])
    
# userList = ["백준아이디", ] -> array 형태로 받기 
# DBid = ["디코아이디":"백준아이디",] 
# DBcoin = ["백준아이디":coin]
# DBid DBcoin은 dictionary 형태로 받기.

def getData():
    global userList, DBid, DBcoin, problems, idList, bytecoin, usercoin, bytebefore
    userList = json.load(open("userList.json"))
    DBid = json.load(open("DBid.json"))
    DBcoin = json.load(open("DBcoin.json"))
    bytecoin = json.load(open("bytecoin.json"))
    usercoin = json.load(open("usercoin.json"))
    bytebefore = json.load(open("bytebefore.json"))
    
def putCoinInfo():
    json.dump(bytecoin, open("bytecoin.json", "w"))
    json.dump(usercoin, open("usercoin.json", "w"))
    json.dump(bytebefore, open("bytebefore.json", "w"))
    json.dump(DBcoin, open("DBcoin.json", "w"))

def putUserInfo():
    json.dump(userList, open("userList.json", "w"))
    json.dump(DBid, open("DBid.json", "w"))
    json.dump(DBcoin, open("DBcoin.json", "w"))

def showbyte():
    embed = discord.Embed(title="BYTECOIN 현황판", description=f"50원 이하로 내려가면 코인이 초기화됩니다.\n판매 수수료: {(1-feers) * 100:.2f}%", color=discord.Color.green())
    for name, value in bytecoin.items():
        embed.add_field(name=f"{name}", value=f"{value} COIN ({bytebefore[name]:+})", inline=False)
    return embed

def embedAdmin():
    embed = discord.Embed(title="권한 부족", description="admin의 권환 필요", color=discord.Color.red())
    return embed
def haveAdmin(ctx):
    if ctx.guild.roles[8] not in ctx.author.roles:
        return 0
    return 1

@tasks.loop(hours=1)
async def TDprob():
    global todaysProbID, todaysProbRank
    todaysSolvedID = []
    pluscoin = int(todaysProbRank * 50 + 2**((todaysProbRank - 1) // 5) * 50)
    url = "https://solved.ac/api/v3/search/problem"
    for dicoName, baekjoon in DBid.items():
        query = f" ~@{baekjoon} id:{todaysProbID}"
        querystring = {"query":query}
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            rtx = json.loads(response.text)
            cnt = rtx["count"]
            if(cnt == 0 and todaysProbID != -1):
                todaysSolvedID.append(dicoName.split('#')[0])
                DBcoin[dicoName] += pluscoin
        except Exception as e:
            print(e)
    if(len(todaysSolvedID) == 0):
        embed = discord.Embed(title="문제 해결자", description="문제 해결자가 존재하지 않습니다.", color=discord.Color.red())
        await bot.get_guild(server_id).get_channel(channel_TD).send(embed=embed)
    else:
        msg = "```"
        for dicoName in todaysSolvedID:
            msg += dicoName + " "
        msg = msg[:-1] + "```"
        embed = discord.Embed(title="문제 해결자", description=msg, color=discord.Color.green())
        embed.add_field(name=f"각 유저에게 {pluscoin} COIN 이 주어집니다.", value="")
        await bot.get_guild(server_id).get_channel(channel_TD).send(embed=embed)
    putCoinInfo()
    url = "https://solved.ac/api/v3/search/problem"
    query =f"lang:ko *{min_LV}..{max_LV}"
    for id in userList:
        query += f" ~@{id}"
    querystring = {"query":query,"sort":"random"}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        rtx = json.loads(response.text)
        msg = f"{min_LV} ~ {max_LV} 사이에서 랜덤한 문제를 뽑았습니다."
        prob = rtx["items"][0]["problemId"]
        rank = rtx["items"][0]["level"]
        todaysProbID = prob
        todaysProbRank = rank
        embed = showproblem(prob)
        embed.set_footer(text=msg)
        await bot.get_guild(server_id).get_channel(channel_TD).send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="오류", description="문제 정보가 없습니다.", color=discord.Color.red())
        await bot.get_guild(server_id).get_channel(channel_TD).send(embed=embed)
    
@tasks.loop(minutes=15)
async def coinchange():
    print("코인 등락!!!")
    for name, value in bytecoin.items():
        diff = int(((r.random() - 0.4875) * 2 / 10 + 1) * value) - value
        if value <= 60 and diff > 0: diff += 2
        elif value <= 100 and diff > 0: diff += 1
        elif value >= 5000 and diff > 0: diff *= 0.95
        elif value >= 10000 and diff > 0: diff *= 0.9
        elif value >= 50000 and diff > 0: diff *= 0.85
        diff = int(diff)
        bytecoin[name] += diff
        if bytecoin[name] <= 50:
            bytecoin[name] = 100
            for dicoName in DBid.keys():
                if usercoin[dicoName][name] > 0:
                    embed = discord.Embed(title=f"{dicoName.split('#')[0]}님!", description=f"{name} {usercoin[dicoName][name]}C 가 휴지조각이 되었어요!", color=discord.Color.red())
                    usercoin[dicoName][name] = 0
                    await bot.get_guild(server_id).get_channel(channel_id).send(embed=embed)
            diff = 0
        bytebefore[name] = diff
        putCoinInfo()
    embed = showbyte()
    await bot.get_guild(server_id).get_channel(channel_id).purge(limit=10000)
    await bot.get_guild(server_id).get_channel(channel_id).send(embed=embed)

# 봇이 켜졌을 때
@bot.event
async def on_ready():
    print(bot.user.name) 
    print('------')
    print("데이터 불러오는 중...")
    try:
        getData()
        TDprob.start()
        print("데이터를 정상적으로 불러왔습니다.")
    except Exception:
        print("데이터를 불러오지 못했습니다.")
        
######################################################
#           BAEKJOON 관련 커맨드 / 함수 작성           #
###################################################### 
# bot 서브 그룹: boj
# 티어 확인: /tier id
# 랜던 문제: /random low high
# 문제 검색: /problem id
# 문제 가져오기: /getproblem

# 티어 확인하기
@boj.command(description="백준 티어를 보여줍니다.")
async def tier(ctx, user_id: Option(str, "백준 아이디를 입력하세요.")):
    url = "https://solved.ac/api/v3/user/show"
    querystring = {"handle":f"{user_id}"}
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers,params=querystring)
    try:
        rtx = json.loads(response.text)
        userTier = int(rtx["tier"])
        userRating = int(rtx["rating"])
        embed = discord.Embed(title=f"{user_id}님의 티어", description=f"{rank_name[userTier]}{rank_imo[rank_name[userTier].split()[0]]} {userRating}", color=discord.Color.green())
        await ctx.respond(embed = embed)
    except Exception:
        embed = discord.Embed(title="대상 오류", description="유저 정보가 없습니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)

@boj.command(description="랜덤 문제를 뽑습니다.")
async def random(ctx, min_lv: Option(str, "최소 티어"), max_lv: Option(str, "최대 티어"), solved: Option(int, "푼 사람 n명 이하 문제만", required=False)):
    if solved == None:
        solved = 100000000
    url = "https://solved.ac/api/v3/search/problem"
    query =f"lang:ko solved:..{solved} *{min_lv}..{max_lv}"
    for id in userList:
        query += f" ~@{id}"
    querystring = {"query":query,"sort":"random"}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        rtx = json.loads(response.text)
        msg = f"{min_lv} ~ {max_lv} 사이에서 랜덤한 문제를 뽑았습니다."
        prob = rtx["items"][0]["problemId"]
        embed = showproblem(prob)
        embed.set_footer(text=msg)
        await ctx.respond(embed = embed)
    except Exception as e:
        embed = discord.Embed(title="오류", description="문제 정보가 없습니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)

@boj.command(description="랜덤 문제를 뽑습니다. (자신이 풀지 않은 문제)")
async def myrandom(ctx, min_lv: Option(str, "최소 티어"), max_lv: Option(str, "최대 티어"), solved: Option(int, "푼 사람 n명 이하 문제만", required=False)):
    if solved == None:
        solved = 100000000
    url = "https://solved.ac/api/v3/search/problem"
    query =f"lang:ko solved:..{solved} *{min_lv}..{max_lv}"
    dicoName = str(ctx.author)
    if dicoName not in DBid.keys():
        embed = discord.Embed(title="오류", description="유저 정보가 없습니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)
        return
    query += f" ~@{DBid[dicoName]}"
    querystring = {"query":query,"sort":"random"}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        rtx = json.loads(response.text)
        print(rtx)
        msg = f"{min_lv} ~ {max_lv} 사이에서 랜덤한 문제를 뽑았습니다."
        prob = rtx["items"][0]["problemId"]
        embed = showproblem(prob)
        embed.set_footer(text=msg)
        await ctx.respond(embed = embed)
    except Exception as e:
        embed = discord.Embed(title="오류", description="문제 정보가 없습니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)
# 문제 검색하기
@boj.command(description="문제 번호로 문제를 검색합니다.")
async def problem(ctx, id: Option(int, "문제 번호")):
    try:
        embed = showproblem(id)
        await ctx.respond(embed = embed)
    except Exception:
        embed = discord.Embed(title="오류", description="문제 정보가 없습니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)

@boj.command(description="랜덤 문제 난이도 범위를 지정합니다.")
async def setlv(ctx, min_lv: Option(str, "최소 티어"), max_lv: Option(str, "최대 티어")):
    try:
        min_LV = min_lv
        max_LV = max_lv
        embed = discord.Embed(title="난이도 설정 완료", description=f"{min_LV} ~ {max_LV}의 난이도로 설정되었습니다.", color=discord.Color.green())
        await ctx.respond(embed = embed)
    except Exception:
        embed = discord.Embed(title="오류", color=discord.Color.red())
        await ctx.respond(embed = embed)
######################################################
#         디스코드 전반적인 커맨드 / 함수 작성          #
###################################################### 
# 역할 확인하기: /myrole
# 역할 부여하기: /register id
# 유저 목록 확인: /userlist
# 메시지 청소: /clear

# 역할 확인하기(디버그용)
@bot.command(description="역할을 확인합니다. (디버그용)")
async def myrole(ctx):
    if not haveAdmin(ctx):
        await ctx.respond(embed = embedAdmin())
        return
    await ctx.respond(ctx.author.roles)

# 역할 부여하기
@bot.command(description="역할을 부여합니다.")
async def register(ctx, user_id: Option(str, "백준 아이디를 입력하세요.")):
    url = "https://solved.ac/api/v3/user/show"
    querystring = {"handle":f"{user_id}"}
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers,params=querystring)
    try:
        rtx = json.loads(response.text)
        userTier = int(rtx["tier"])
        only_rank = rank_name[userTier].split(' ')[0]
        
        dicoName = str(ctx.author)
        if (dicoName in DBid) and (DBid[dicoName] != user_id):
            embed = discord.Embed(title="올바르지 않은 아이디", description="가입한 백준 아이디로 명령어를 실행해주세요", color=discord.Color.red())
            await ctx.respond(embed = embed)
            return
        if dicoName not in DBid:
            if user_id in userList:
                embed = discord.Embed(title="중복 가입", description="해당 백준 아이디로 가입한 유저가 있습니다.", color=discord.Color.red())
                await ctx.respond(embed = embed)
                return
            else:
                DBid[dicoName] = user_id
                DBcoin[dicoName] = 500
                userList.append(user_id)
                usercoin[dicoName] = dict.fromkeys(list(bytecoin.keys()), 0)
                try:
                    putUserInfo()
                    putCoinInfo()
                except Exception as e:
                    print("유저 정보를 저장하지 못했습니다.")
                    print("에러 정보")
                    print("-------------")
                    print(e)
                embed = discord.Embed(title=f"{dicoName.split('#')[0]}님 환영합니다!", description=f"기본 {DBcoin[dicoName]} COIN이 주어집니다.", color=discord.Color.green())
                await ctx.respond(embed = embed)
            
        if userTier == 0:
            embed = discord.Embed(title="UNRATED", description=f"브론즈{rank_imo['Bronze']} 이상의 유저에게만 역할이 부여됩니다.", color=discord.Color.red())
            await ctx.respond(embed = embed)
        else:
            await ctx.author.add_roles(bot.get_guild(server_id).get_role(role_id[only_rank]))
            embed = discord.Embed(title=f"{only_rank.upper()}", description=f"{str(ctx.author).split('#')[0]}님에게 {only_rank}{rank_imo[only_rank]}가 부여되었습니다.", color=discord.Color.green())
            await ctx.respond(embed = embed)
    except Exception as e:
        embed = discord.Embed(title="대상 오류", description="해당 유저가 존재하지 않습니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)

# 유저 목록 확인
@bot.command(description="가입된 유저 목록을 확인합니다.")
async def userlist(ctx):
    msg = "`"
    for key, val in DBid.items():
        msg += f"[{key.split('#')[0]} : {val}] "
    msg = msg[:-1]
    msg += "`"
    if len(DBid) != 0:
        embed = discord.Embed(title="가입 유저 목록", description=msg, color=discord.Color.green())
    else:
        embed = discord.Embed(title="대상이 없습니다.", description="가입된 유저가 없거나 데이터가 손상되었습니다.", color=discord.Color.red())
    await ctx.respond(embed = embed)
        
# 메시지 청소: /clear
@bot.command(description="메시지를 삭제합니다.")
async def clear(ctx, amount: Option(int, "지울 메시지의 수", required=False)):
    if amount == None:
        amount = 10000
    if not haveAdmin(ctx):
        await ctx.respond(embed = embedAdmin())
        return
    await ctx.channel.purge(limit=amount)
    embed = discord.Embed(title="메시지 삭제", description=f"{amount}개의 메시지가 삭제되었습니다.", color=discord.Color.green())
    await ctx.respond(embed=embed)
######################################################
#         COIN 시스템 관련 커맨드 / 함수 작성          #
######################################################   
# bot 서브 그룹: coin
# COIN 현황 보기: /current
# COIN 보내기: /send A coin
# COIN 관리: /set A coin
coin = bot.create_group("coin")

# COIN 현황 보기
@coin.command(description="보유한 COIN을 확인합니다.")
async def current(ctx):
    dicoName = str(ctx.author)
    if dicoName in DBid:
        embed = discord.Embed(title=f"{dicoName.split('#')[0]}님의 잔액", description=f"{DBcoin[dicoName]} COIN", color=discord.Color.green())
        await ctx.respond(embed = embed)
    else:
        embed = discord.Embed(title="미가입 상태", description="/register 명령어를 사용해주세요.", color=discord.Color.red())
        await ctx.respond(embed = embed)



# COIN 보내기
@coin.command(description="COIN 을 다른 유저에게 보냅니다.")
async def send(ctx, user: Option(str, "유저", autocomplete=getIDList), coin: Option(int, "보낼 코인")):
    me = str(ctx.author)
    if user not in DBid:
        embed = discord.Embed(title="대상 오류", description=f"{user.split('#')[0]}님이 가입되었는지 확인해주세요.", color=discord.Color.red())
        await ctx.respond(embed = embed)
        return
    if DBcoin[me] < coin:
        embed = discord.Embed(title="잔액 부족", description=f"잔액: {DBcoin[me]} COIN", color=discord.Color.red())
        await ctx.respond(embed = embed)
    elif coin <= 0:
        embed = discord.Embed(title="입력 COIN 0 이하", description="양수 값의 COIN 을 넣어주세요.", color=discord.Color.red())
        await ctx.respond(embed = embed)
    else:
        DBcoin[me] -= coin
        DBcoin[user] += coin
        embed = discord.Embed(title="송금 완료", description=f"{user.split('#')[0]}님에게 {coin} COIN을 보냈습니다.", color=discord.Color.green())
        embed.add_field(name=f"{me.split('#')[0]}", value=f"{DBcoin[me]} COIN")
        embed.add_field(name=f"{user.split('#')[0]}", value=f"{DBcoin[user]} COIN")
        try:
            json.dump(DBcoin, open("DBcoin.json", "w"))
        except Exception as e:
            print(e)
        await ctx.respond(embed = embed)

# COIN 설정하기
@coin.command(description="COIN 을 임의로 설정합니다. (관리자용)")
async def cset(ctx, user: Option(str, "유저", autocomplete=getIDList), coin: Option(int, "COIN")):
    if not haveAdmin(ctx):
        await ctx.respond(embed = embedAdmin())
        return
    if user not in DBid:
        embed = discord.Embed(title="대상 오류", description=f"{user.split('#')[0]}님이 가입되었는지 확인해주세요.", color=discord.Color.red())
        await ctx.respond(embed = embed)
        return
    else:
        DBcoin[user] += coin
        if DBcoin[user] < 0: 
            DBcoin[user] = 0
            coin -= DBcoin[user]
        embed = discord.Embed(title="설정 완료", 
            description=f"{user.split('#')[0]}님의 잔액이 {DBcoin[user] - coin} => {DBcoin[user]} COIN 으로 설정되었습니다.", color=discord.Color.green())
        try:
            json.dump(DBcoin, open("DBcoin.json", "w"))
        except Exception as e:
            print(e)
        await ctx.respond(embed = embed)

# BYTECOIN 현황 보기: /bytecoin
@coin.command(description="현재 BYTECOIN 현황을 확인합니다.")
async def bytecoin(ctx):
    await ctx.respond(embed = showbyte())
    
async def getcoinList(ctx: discord.AutocompleteContext):
    return sorted([i for i in bytecoin.keys()])

@coin.command(description="보유한 BYTECOIN 을 확인합니다.")
async def mybytecoin(ctx):
    dicoName = str(ctx.author)
    msg = ""
    for key, value in usercoin[dicoName].items():
        msg += f"[{key}: {value}] "
    msg = msg[:-1]
    embed = discord.Embed(title=f"{dicoName.split('#')[0]}님의 BYTECOIN", description=f"`{msg}`", color=discord.Color.green())
    await ctx.respond(embed = embed)

@coin.command(description="BYTECOIN 을 구매합니다.")
async def buycoin(ctx, name: Option(str, "BYTECOIN", autocomplete=getcoinList), cnt: Option(int, "개수")):
    dicoName = str(ctx.author)
    if name not in bytecoin.keys():
        embed = discord.Embed(title="오류", description="해당 코인이 없습니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)
        return
    price = bytecoin[name] * cnt
    if price <= DBcoin[dicoName]:
        DBcoin[dicoName] -= price
        usercoin[dicoName][name] += cnt
        embed = discord.Embed(title="구매 성공", description=f"{name} {cnt}C 구매하였습니다.", color=discord.Color.green())
        embed.add_field(name="잔액", value=f"{DBcoin[dicoName]} COIN")
        putCoinInfo()
        await ctx.respond(embed = embed)
    else:
        embed = discord.Embed(title="잔액 부족", description="잔액이 부족합니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)

@coin.command(description="BYTECOIN 을 판매합니다.")
async def sellcoin(ctx, name: Option(str, "BYTECOIN", autocomplete=getcoinList), cnt: Option(int, "개수")):
    dicoName = str(ctx.author)
    if name not in bytecoin.keys():
        embed = discord.Embed(title="오류", description="해당 코인이 없습니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)
        return
    if usercoin[dicoName][name] >= cnt:
        DBcoin[dicoName] += int(bytecoin[name] * cnt * feers)
        usercoin[dicoName][name] -= cnt
        embed = discord.Embed(title="판매 성공", description=f"{name} {cnt}C 판매하였습니다. (판매 수수료: {(1 -feers) * 100:.2f}%)", color=discord.Color.green())
        embed.add_field(name="잔액", value=f"{DBcoin[dicoName]} COIN")
        putCoinInfo()
        await ctx.respond(embed = embed)
    else:
        embed = discord.Embed(title="코인 부족", description="코인이 부족합니다.", color=discord.Color.red())
        await ctx.respond(embed = embed)

chc = ["BYTECOIN 가격", "BYTECOIN 보유", "COIN 잔액"]
@coin.command(description="RESET")
async def reset(ctx, choice: Option(str, "선택지", choices=chc)):   
    if not haveAdmin(ctx):
        await ctx.respond(embed = embedAdmin())
        return 
    if choice not in chc:
        embed = discord.Embed(title="오류", description="선택지 중에 하나를 골라주세요.", color=discord.Color.red())
        await ctx.respond(embed = embed)
    else:
        if choice == chc[0]:
            for key in bytecoin.keys():
                bytecoin[key] = int(100 * (r.random() * 2 + 0.5))
        elif choice == chc[1]:
            for dicoName in DBid.keys():
                for coinName in bytecoin.keys():
                    usercoin[dicoName][coinName] = 0
        elif choice == chc[2]:
            for dicoName in DBid.keys():
                DBcoin[dicoName] = 500
        
        embed = discord.Embed(title=f"{choice} 초기화", description="초기화가 완료되었습니다.", color=discord.Color.green())
        await ctx.respond(embed = embed)
        putCoinInfo()   

@coin.command(description="BYTECOIN 시작")
async def start(ctx):
    if not haveAdmin(ctx):
        await ctx.respond(embed = embedAdmin())
        return 
    coinchange.start()
    embed = discord.Embed(title="BYTECOIN 이 시작됩니다.", description="15분 간격으로 가격이 변동됩니다.", color=discord.Color.green())
    await ctx.respond(embed = embed)
    
@coin.command(description="BYTECOIN 중단")
async def stop(ctx):
    if not haveAdmin(ctx):
        await ctx.respond(embed = embedAdmin())
        return 
    coinchange.stop()
    embed = discord.Embed(title="BYTECOIN 이 중단됩니다.", description="시작하려면 /coin start 를 해주세요.", color=discord.Color.green())
    await ctx.respond(embed = embed)   
bot.run() #토큰 (String " ")