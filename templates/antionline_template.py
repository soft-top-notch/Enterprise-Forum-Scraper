# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate


class AntiOnlineParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "antionline.com"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*u=(\w+)\&')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//li[contains(@class,"postcontainer")]'
        self.header_xpath = '//li[contains(@class,"postcontainer")]'
        self.date_xpath = './/span[@class="date"]//text()'
        self.title_xpath = '//span[contains(@class,"threadtitle")]//descendant::text()'
        self.post_text_xpath = './/div[contains(@class,"postbody")]//div[@class="content"]//descendant::text()[not(ancestor::div[@class="quote_container"])]'
        self.comment_block_xpath = './/div[contains(@class,"posthead")]//span[@class="nodecontrols"]/a//text()'
        self.avatar_xpath = './/div[contains(@class,"userinfo")]//a[@class="postuseravatar"]//img/@src'
        self.avatar_ext = 'jpg'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: (self.thread_name_pattern.search(x).group(1),
                           self.pagination_pattern.search(x).group(1)))

        return sorted_files

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        if date_block:
            date_blocks = ' '.join(date_block)
            date = date_blocks.strip()
        else:
            return None

        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""

        return ""

    def get_author(self, tag):
        author = tag.xpath(
            './/a[contains(@class,"username")]//descendant::text()'
        )
        if not author:
            author = tag.xpath(
                './/span[contains(@class,"username")]//descendant::text()'
            )
        author = author[0].strip() if author else None
        return author
