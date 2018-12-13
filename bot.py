from configparser import ConfigParser

from discord.ext import commands

from gw2wiki import wikibot

conf = ConfigParser()
conf.read('conf.ini')
token = conf.get('DISCORD', 'token')
bot = commands.Bot(command_prefix='$')


@bot.command(name='上传页面缺失图片')
async def upload_image(ctx, *args):
    for page in args:
        await ctx.send('上传{}中缺失的图片'.format(page))
        for i in wikibot.upload_images_by_page(page):
            await ctx.send(i)


@bot.command(name='上传页面缺失图片1')
async def upload_image_v1(ctx, *args):
    for page in args:
        await ctx.send('上传{}中缺失的图片'.format(page))
        for i in wikibot.upload_images_by_page(page, wiki_version=1):
            await ctx.send(i)

bot.run(token)
