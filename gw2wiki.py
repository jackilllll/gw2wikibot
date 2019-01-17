import json
import re
import time
from configparser import ConfigParser
from urllib.parse import urljoin

import mwclient
import requests
from requests_html import HTMLSession

conf = ConfigParser()
conf.read('conf.ini')
username = conf.get('WIKI', 'username')
password = conf.get('WIKI', 'password')


class Gw2WikiBot:
    def __init__(self, username, password):
        self.site = mwclient.Site('gw2.huijiwiki.com')
        self.site.login(username, password)

    def parse_text(self, text):
        return self.site.expandtemplates(text)

    @staticmethod
    def parse_image_name(name):
        p = re.compile('[\d]+px-')
        return p.sub('', name)

    def pre_parse(self, text):
        """
        预解析wiki文本,适用于开销较大的页面
        缺点：解析出来的内容不易维护
        :param text:
        :return:
        """
        all_text = text
        p = re.compile('(({{.*}}\n){2,20})')
        r = p.findall(text)
        group_count = len(r)
        yield '正在解析模板,共{}组text需要被解析'.format(group_count)
        for index, i in enumerate(r):
            old = i[0]
            new = self.parse_text(old)
            yield '解析进度：{}/{}'.format(index + 1, group_count)
            all_text = all_text.replace(old, new)
        yield all_text

    @staticmethod
    def get_wiki_last_id(data_type):
        url = 'https://gw2.huijiwiki.com/api/rest_v1/namespace/data' \
              '?filter=%7B%22_id%22%3A%7B%22%24regex%22%3A%22%5EData%3A{}%22%7D%7D&sort_by=-id&page=1&pagesize=1'. \
            format(data_type.title())
        last_info = requests.get(url).json()
        last_id = last_info['_embedded'][0]["id"]
        return last_id

    def get_sync_ids(self, data_type, init=False):
        if init:
            all_data_ids = requests.get("https://api.guildwars2.com/v2/{}s".format(data_type)).json()
            return all_data_ids
        else:
            all_data_ids = requests.get("https://api.guildwars2.com/v2/{}s".format(data_type)).json()
            last_id = self.get_wiki_last_id(data_type)
            index_of_last = all_data_ids.index(last_id)
            need_sync_data_ids = sorted(set(all_data_ids[index_of_last + 1:]))
            self.__setattr__('need_sync_{}_ids'.format(data_type), need_sync_data_ids)
            return need_sync_data_ids

    def get_and_upload_data(self, data_type, data_id):
        wiki_name = 'Data:{}/{}.json'.format(data_type.title(), data_id)

        # 获取data en
        data_en = requests.get("https://api.guildwars2.com/v2/{}s/{}".format(data_type, data_id)).json()
        # 获取data zh
        data = requests.get("https://api.guildwars2.com/v2/{}s/{}?lang=zh".format(data_type, data_id)).json()
        # 组合data
        # 拥有name属性的data处理
        if 'name' in data:
            data.update({
                "name_en": data_en["name"]
            })

        return self.upload_data(wiki_name, data)

    def upload_data(self, wiki_name, data):
        wiki_content = json.dumps(data, ensure_ascii=False)
        page = self.site.pages[wiki_name]
        if not page.exists:
            page.save(wiki_content, 'upload data by bot')
            yield ('{}-上传成功'.format(wiki_name))
        else:
            page.save(wiki_content, 'update data by bot')
            yield ('{}-已经存在(完成更新)'.format(wiki_name))

    def update(self, data_type, data_ids=None, init=False):
        """
        指定更新数据的类型，开始同步api数据
        :param data_ids: [数据ID]
        :param data_type: 数据类型 ['item','skill',...]
        :param init: 是否初始化，用于第一次搬运一个新类型的数据
        :return:
        """

        if data_ids:
            need_update_ids = data_ids
        else:
            need_update_ids = self.get_sync_ids(data_type, init)
            yield ("{}有{}个项需要更新".format(data_type, len(need_update_ids)))
        for data_id in need_update_ids:
            r = self.get_and_upload_data(data_type, data_id)
            for i in r:
                yield i

    def upload_images_by_page(self, page_name, wiki_version=2):
        """
        自动搬运页面下缺失的图片,默认从gw2 wiki搬运.
        :param wiki_version: wiki版本 [1,2]
        :param page_name: 页面名称
        :return:
        """
        page = self.site.pages[page_name]
        need_upload_images = [img for img in page.images() if not img.exists]
        all_account = len(need_upload_images)
        fail_count = 0
        yield ('====开始上传【{}】中缺失的图片({}张)===='.format(page_name, all_account))
        for index, img in enumerate(need_upload_images):
            parsed_image_name = self.parse_image_name(img.page_title)
            origin_url = self.get_wiki_image_url(wiki_version, parsed_image_name)
            time.sleep(1)
            if origin_url:
                try:
                    self.site.upload(filename=parsed_image_name, url=origin_url)
                    yield ('【{}】上传成功({}/{})'.format(parsed_image_name, index + 1, all_account))
                except Exception as e:
                    print(e)
                    fail_count += 1
                    yield ('【{}】上传失败({}/{})'.format(parsed_image_name, index + 1, all_account))
            else:
                fail_count += 1
                yield ('【{}】上传失败(在wiki中找不到该图片)({}/{})'.format(parsed_image_name, index + 1, all_account))

        yield ('====【{}】中缺失的图片上传完毕(成功：{},失败:{})===='.format(page_name, all_account - fail_count, fail_count))

    def mv(self, en_name, zh_name, wiki_version=2):
        """
        从英文wiki搬运页面到中文wiki,并自动处理图片上传
        :param wiki_version: 1 or 2
        :param en_name: 英文wiki页面名称
        :param zh_name: 中文wiki页面名称
        :return:
        """
        v = '' if wiki_version == 1 else 2
        page = self.site.pages[zh_name]
        if not page.exists:
            en_page_url = 'https://wiki.guildwars{}.com/index.php?title={}&action=raw'.format(v, en_name)
            r = requests.get(en_page_url)
            r = page.save(self.en_wiki_text_parse(r.text), '{}>{}(机器人搬运)'.format(en_name, zh_name))
            if r['result'] == 'Success':
                yield '页面:{}搬运成功，正在上传图片...'.format(zh_name)
                for i in self.upload_images_by_page(zh_name, wiki_version=wiki_version):
                    yield i
                yield '页面:{}搬运完成,图片上传完毕'.format(zh_name)
        else:
            yield '页面已经存在无需搬运'

    @staticmethod
    def en_wiki_text_parse(text):
        # 工程师模板替换
        parsed_text = text.repalce('{{en}}', '{{eng}}')
        return parsed_text

    def tmp_mv(self, en_name):
        """
        从英文wiki搬运页面到中文wiki,并自动处理图片上传
        :param en_name: 模板的英文名称，不带Template:
        :return:
        """
        page = self.site.pages[en_name]
        if not page.exists:
            en_page_url = 'https://wiki.guildwars2.com/index.php?title=Template:{}&action=raw'.format(en_name)
            r = requests.get(en_page_url)
            r = page.save(r.text, '{}创建(机器人搬运)'.format(en_name))
            if r['result'] == 'Success':
                yield '模板:{}搬运成功，正在上传图片...'.format(en_name)
                for i in self.upload_images_by_page(en_name):
                    yield i
                yield '模板:{}搬运完成,图片上传完毕'.format(en_name)
        else:
            yield '模板已经存在无需搬运'

    @staticmethod
    def get_wiki_image_url(wiki_version, image_name):
        """
        从1代或者2代wiki中获取图片的url
        :param wiki_version: wiki版本
        :param image_name: 图片名称.jpg
        :return: 图片url
        """
        v = '' if wiki_version == 1 else 2
        base_file_url = 'https://wiki.guildwars{}.com/wiki/File:'.format(v)
        image_page_url = base_file_url + image_name
        request = HTMLSession()
        r = request.get(image_page_url)
        a = r.html.xpath('//*[@id="file"]/a/img')
        if a:
            image_base_url = 'https://wiki.guildwars{}.com'.format(v)
            image_url = urljoin(image_base_url, a[0].attrs['src'])
            return image_url
        else:
            return None


wikibot = Gw2WikiBot(username=username, password=password)

if __name__ == '__main__':
    # text = '{{#invoke:API|filter|item|name|永恒}}'
    # r = wikibot.parse_text(text)
    for i in wikibot.update('recipe', init=True):
        print(i)
