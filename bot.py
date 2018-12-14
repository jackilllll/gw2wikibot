import time
from configparser import ConfigParser

from discord.ext import commands

from gw2wiki import wikibot

conf = ConfigParser()
conf.read('conf.ini')
token = conf.get('DISCORD', 'token')
bot = commands.Bot(command_prefix='$')


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


@bot.command(name='上传页面缺失图片')
async def upload_image(ctx, *args):
    for page in args:
        await ctx.send('====开始上传【{}】中缺失的图片===='.format(page))
        for i in wikibot.upload_images_by_page(page):
            print(i)
            await ctx.send(i)
        await ctx.send('====【{}】中缺失的图片上传完毕===='.format(page))
        time.sleep(2)


@bot.command(name='上传页面缺失图片1')
async def upload_image_v1(ctx, *args):
    for page in args:
        await ctx.send('====开始上传【{}】中缺失的图片===='.format(page))
        for i in wikibot.upload_images_by_page(page, wiki_version=1):
            print(i)
            await ctx.send(i)
        await ctx.send('====【{}】中缺失的图片上传完毕===='.format(page))
        time.sleep(2)


if __name__ == '__main__':
    bot.run(token)
