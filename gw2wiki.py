import json
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

        self.upload_data(wiki_name, data)

    def upload_data(self, wiki_name, data):
        wiki_content = json.dumps(data, ensure_ascii=False)
        page = self.site.pages[wiki_name]
        if not page.exists:
            page.save(wiki_content, 'upload data by bot')
            print('{}-上传成功'.format(wiki_name))
        else:
            print('{}-已经存在'.format(wiki_name))

    def update(self, data_type, init=False):
        """
        指定更新数据的类型，开始同步api数据
        :param data_type: 数据类型 ['item','skill',...]
        :param init: 是否初始化，用于第一次搬运一个新类型的数据
        :return:
        """
        need_update_ids = self.get_sync_ids(data_type, init)
        print("{}有{}个项需要更新".format(data_type, len(need_update_ids)))
        for data_id in need_update_ids:
            self.get_and_upload_data(data_type, data_id)

    def upload_images_by_page(self, page_name, wiki_version=2):
        """
        自动搬运页面下缺失的图片,默认从gw2 wiki搬运.
        :param wiki_version: wiki版本 [1,2]
        :param page_name: 页面名称
        :return:
        """
        page = self.site.pages[page_name]
        for image in page.images():
            img = self.site.images[image.page_title]
            if not img.exists:
                origin_url = self.get_wiki_image_url(wiki_version, img.page_title)
                time.sleep(1)
                try:
                    self.site.upload(filename=img.page_title, url=origin_url)
                    yield ('{} 上传成功'.format(img.page_title))
                except Exception as e:
                    print(e)
                    yield ('{} 上传失败'.format(img.page_title))

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
        image_base_url = 'https://wiki.guildwars{}.com'.format(v)
        image_url = urljoin(image_base_url, a[0].attrs['src'])
        return image_url


wikibot = Gw2WikiBot(username=username, password=password)
