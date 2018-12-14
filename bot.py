import time
from configparser import ConfigParser

from discord.ext import commands

from gw2wiki import wikibot

conf = ConfigParser()
conf.read('conf.ini')
token = conf.get('DISCORD', 'token')
bot = commands.Bot(command_prefix='$')


@bot.command(name="help")
async def _help(ctx):
    h = '''    
mv：从英文wiki搬运页面 eg: mv "Lion's Arch" 狮子拱门
fpi：即fix page images ,自动搬运页面中缺失的图片(搬运多个页面用空格隔开)eg: fpi 狮子拱门 神秘熔炉
fpi1: 从1代wiki中搬运图片,用法同上
    '''
    await ctx.send(h)


@bot.command()
async def mv(ctx, en, zh):
    for res in wikibot.mv(en, zh):
        print(res)
        await ctx.send(res)


@bot.command()
async def update(ctx, data_type):
    for res in wikibot.update(data_type):
        print(res)
        await ctx.send(res)


@bot.command(name='fpi')
async def upload_image(ctx, *args):
    for page in args:
        for i in wikibot.upload_images_by_page(page):
            print(i)
            await ctx.send(i)
        time.sleep(2)


@bot.command(name='fpi1')
async def upload_image_v1(ctx, *args):
    for page in args:
        for i in wikibot.upload_images_by_page(page, wiki_version=1):
            print(i)
            await ctx.send(i)
        time.sleep(2)


if __name__ == '__main__':
    bot.run(token)
