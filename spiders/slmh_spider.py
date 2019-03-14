import scrapy
import os
import urllib
from urllib import parse
import zlib
import re
import requests
from scrapy_splash import SplashRequest
from scrapy.http import HtmlResponse

class slmh(scrapy.Spider):
    name = 'Cartoon'
    global tagdoman
    global document
    tagdoman = 'http://www.chuixue.net'  # 主机名
    # 吹雪搜索规则
    # keyword 需经过 UrlEncode编码
    keyword = input('请输入漫画名:')
    r = requests.get('http://www.chuixue.net/e/search/?searchget=1&show=title,player,playadmin,pinyin&keyboard=' + parse.quote(keyword.encode('gb2312')))
    body = r.text
    response = HtmlResponse(url=r.url, body=body, encoding='utf-8')
    items = response.css('.dmList ul li a.pic img::attr(alt)').extract()
    if len(items) > 1:
        for index in range(len(items)):
            print('('+str(index)+') '+str(items[index])+'')
        while True:
            tag_index = input('请输入要下载的序号:')
            if tag_index.isdigit() and int(tag_index) <= len(items):
                real_link = response.css('.dmList ul li a.pic::attr(href)').extract()[int(tag_index)]  # 漫画列表页
                Folder_name = response.css('.dmList ul li a.pic img::attr(alt)').extract()[int(tag_index)]  # 漫画名
                break

    else:
        real_link = response.css('.dmList ul li a.pic::attr(href)').extract_first()  # 漫画列表页
        Folder_name = response.css('.dmList ul li a.pic img::attr(alt)').extract_first()  # 漫画名

    document = 'C:/scrapylearn/slmh/cartoon/'+Folder_name  # 设置漫画名为文件夹名
    # document = input('请输入保存路径:')
    start_urls = [''+tagdoman + real_link+'']  # 拼接完整漫画列表页

    def parse(self, response):
        itemslist = response.css('.plist ul li')  # 提取漫画目录
        print(response)
        for items in itemslist:  # 循环获取每一条
            itemlink = tagdoman + items.css('a::attr(href)').extract_first()  # 章节链接
            yield SplashRequest(itemlink
                                , self.comics_parse
                                , args={'wait': '0.5'}
                                # ,endpoint='render.json'
                                )

    def comics_parse(self, response):
        list_title = response.xpath("//h1/text()").extract_first()  # 翻页器
        list_title_pagenum = response.xpath("//h1//span[@id='viewpagename']/text()").extract_first()  # 翻页器

        page_list = response.xpath("//span[@id='selectpage1']//select//option/@value").extract()  # 翻页器
        img_src = response.xpath("//img[@id='viewimg']/@src").extract()
        # print(list_title.replace(' ', ''))
        # print(list_title_pagenum)
        # print(img_src[0])
        self.save_img(list_title_pagenum, list_title.replace(' ', ''), img_src[0])
        for pagenum in page_list:
            next_page = re.sub(r'\?.*', '', response.url) + '?page='+pagenum
            yield SplashRequest(next_page
                                , self.comics_parse
                                , args={'wait': '0.5'}
                                # ,endpoint='render.json'
                                )

    def save_img(self, img_mun, title, img_url):
        # 将图片保存到本地
        self.log('saving pic: ' + img_url)

        # 保存漫画的文件夹
        if not os.path.exists(document):
            os.makedirs(document)

        # 每部漫画的文件名以标题命名
        comics_path = document + '/' + title
        exists = os.path.exists(comics_path)
        if not exists:
            self.log('create document: ' + title)
            os.makedirs(comics_path)

        # 每张图片以页数命名
        pic_name = comics_path + '/' + img_mun + '.jpg'

        # 检查图片是否已经下载到本地，若存在则不再重新下载
        exists = os.path.exists(pic_name)
        if exists:
            self.log('pic exists: ' + pic_name)
            return

        try:
            user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
            headers = {'User-Agent': user_agent}

            req = urllib.request.Request(img_url, headers=headers)
            response = urllib.request.urlopen(req, timeout=30)

            # 请求返回到的数据
            data = response.read()

            # 若返回数据为压缩数据需要先进行解压
            if response.info().get('Content-Encoding') == 'gzip':
                data = zlib.decompress(data, 16 + zlib.MAX_WBITS)

            # 图片保存到本地
            fp = open(pic_name, "wb")
            fp.write(data)
            fp.close

            self.log('save image finished:' + pic_name)

        except Exception as e:
            self.log('save image error.')
            self.log(e)