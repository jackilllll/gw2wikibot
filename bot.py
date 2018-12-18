import time
from configparser import ConfigParser

from discord.ext import commands

from gw2wiki import wikibot

conf = ConfigParser()
conf.read('conf.ini')
token = conf.get('DISCORD', 'token')
bot = commands.Bot(command_prefix='$')


@bot.command(name='tmv')
async def tmv(ctx, *args):
    """
    从英文wiki搬运模板(不需要加前缀——templates:) eg: mv "Skill fact" "infobox npc"
    :param ctx:
    :return:
    """
    for tmp_name in args:
        for res in wikibot.mv(tmp_name):
            print(res)
            await ctx.send(res)


@bot.command()
async def mv(ctx, en, zh):
    """
    从英文wiki搬运页面 eg: mv "Lion's Arch" 狮子拱门
    :param ctx:
    :param en:
    :param zh:
    :return:
    """
    for res in wikibot.mv(en, zh):
        print(res)
        await ctx.send(res)


@bot.command()
async def update(ctx, data_type, data_ids=None):
    """
    eg: update item 23233,22224
    :param data_type: 数据类型 [item,skill,achievement]
    :param data_ids: 指定数据ids，单独更新数据 逗号隔开
    :return:
    """
    ids = []
    if data_ids:
        ids = [int(i) for i in data_ids.split(',')]
    for res in wikibot.update(data_type, ids):
        print(res)
        await ctx.send(res)


@bot.command(name='fpi')
async def upload_image(ctx, *args):
    """
    即fix page images ,自动搬运页面中缺失的图片(搬运多个页面用空格隔开)eg: fpi 狮子拱门 神秘熔炉
    :param ctx:
    :param args:
    :return:
    """
    for page in args:
        for i in wikibot.upload_images_by_page(page):
            print(i)
            await ctx.send(i)
        time.sleep(2)


@bot.command(name='fpi1')
async def upload_image_v1(ctx, *args):
    """
    从1代wiki中搬运图片,用法同fpi
    :param ctx:
    :param args:
    :return:
    """
    for page in args:
        for i in wikibot.upload_images_by_page(page, wiki_version=1):
            print(i)
            await ctx.send(i)
        time.sleep(2)


if __name__ == '__main__':
    bot.run(token)
