from discord import FFmpegPCMAudio
import discord
from os.path import abspath
import asyncio
from discord.ext import commands
from config import settings
intents = discord.Intents.default()
intents.guilds=True
bot = commands.Bot(command_prefix=settings['prefix'], intents=intents)
from youtube_dl import YoutubeDL
discord.opus.load_opus(abspath(__file__)[:-7] + 'libopus-0.x64.dll')
servers = {}

YDL_OPTIONS = {'quiet': True, 'format': 'bestaudio/best', 'skip_download': True, "cookiefile": "youtube.com_cookies.txt"}

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

def anowerOne(ctx):
    global servers
    serverid = ctx.message.guild.id
    servers[serverid].update({"isPlaying": False})
    coro = playsong(ctx)
    fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
    fut.result()

async def playsong(ctx):
    global servers
    serverid = ctx.message.guild.id
    voice_channel = ctx.message.author.voice.channel
    if servers[serverid]["loop"] is not None:
        servers[serverid]["vc"].play(FFmpegPCMAudio(source=servers[serverid]["loop"][0], executable='ffmpeg.exe', **FFMPEG_OPTIONS), after=lambda e: anowerOne(ctx))
        servers[serverid].update({"isPlaying": True})
    elif len(servers[serverid]["playlist"]) > 0:
        if servers[serverid]["vc"] == None:
            servers[serverid].update({"vc": await voice_channel.connect()})
        servers[serverid]["song"] = servers[serverid]["playlist"].pop(0)
        servers[serverid]["vc"].play(FFmpegPCMAudio(source=servers[serverid]["song"][0], executable='ffmpeg.exe', **FFMPEG_OPTIONS), after=lambda e: anowerOne(ctx))
        await ctx.channel.send('**Сейчас играет**:notes: `'+servers[serverid]["song"][1] + '`')
        servers[serverid].update({"isPlaying": True})
    else:
        await stop(ctx)

@bot.command(aliases=['play', 'P','PLAY'])
async def p(ctx, *arg):
    global servers
    serverid = ctx.message.guild.id
    if servers.get(serverid) is None:
        servers.update({serverid: {'vc': None, 'loop': None, 'isPlaying': False, 'song': None, 'playlist': []}})
    if arg != ():
        arg = " ".join(arg)
        if ctx.message.author.voice!= None:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                ydl.cache.remove()
                if "https://www.youtube.com/watch" in arg:
                    #try:
                        info = ydl.extract_info(arg)
                        if '_type' in info.keys():
                            if info['_type'] == 'playlist':
                                for i in info['entries']:
                                    print(i['url'], i['title'])
                                    servers[serverid]["playlist"].append([i['url'], i['title']])
                                await ctx.channel.send('**Плейлист добавлен в плейлист!**')
                                if not servers[serverid]["isPlaying"]:
                                    await playsong(ctx)
                            else:
                                await ctx.channel.send(':x:**Вы указали нерабочую ссылку!**')
                        else:
                            servers[serverid]["playlist"].append([info['url'], info['title']])
                            if not servers[serverid]["isPlaying"]:
                                await playsong(ctx)
                            else:
                                await ctx.channel.send('`' + servers[serverid]["playlist"][len(servers[serverid]["playlist"]) - 1][1] + '` **добавленно в плейлист!**')
                    # except:
                    #      await ctx.channel.send(':x:**Вы указали нерабочую ссылку!**')
                else:
                    await ctx.channel.send('**Ищем**:mag_right: `' + arg + '`')
                    info = ydl.extract_info("ytsearch:" + arg)
                    if len(info['entries']) == 0:
                        await ctx.channel.send(':x:**По данному запросу ничего не найдено!** ')
                    else:
                        servers[serverid]["playlist"].append([info['entries'][0]['url'], info['entries'][0]['title']])
                        if not servers[serverid]["isPlaying"]:
                            await playsong(ctx)
                        else:
                            await ctx.channel.send('`' + info['entries'][0]['title'] + '` **добавленно в плейлист!**')
        else:
            await ctx.channel.send(':x:**Вы не находитесь в звуковом канале!**')
    else:
        await ctx.channel.send(':x:**Вы не указали аргумент для поиска!**')

@bot.command(aliases=['s','FS', 'S', 'fs', 'forceskip'])
async def skip(ctx):
    global servers
    serverid = ctx.message.guild.id
    if servers[serverid]["vc"] != None:
        if servers[serverid]["vc"].is_playing():
            if servers[serverid]["loop"] is not None:
                servers[serverid]["loop"] = None
            servers[serverid]["vc"].stop()
            await ctx.channel.send(':fast_forward:**Пропущено!**')
        else:
            await ctx.channel.send(':x:**В данный момент ничего не проигрывается!**')
    else:
        await ctx.channel.send(':x:**В данный момент ничего не проигрывается!**')

@bot.command(aliases=['st', 'STOP', 'ST'])
async def stop(ctx):
    global servers
    serverid = ctx.message.guild.id
    servers[serverid].update({"isPlaying": False})
    if servers[serverid]["vc"] != None:
        await servers[serverid]["vc"].disconnect()
        servers.pop(serverid)
    else:
        await ctx.channel.send(':x:**В данный момент ничего не проигрывается!**')

@bot.command(aliases=['l','LOOP', 'lp'])
async def loop(ctx):
    global servers
    serverid = ctx.message.guild.id
    if servers[serverid]["song"] is not None:
        servers[serverid]["loop"] = servers[serverid]["song"]
        await ctx.channel.send(':repeat:`' + servers[serverid]["loop"][1] + '`**поставленно на реплей!**')
    else:
        await ctx.channel.send(':x:**В данный момент ничего не проигрывается!**')

bot.run(settings['token'])