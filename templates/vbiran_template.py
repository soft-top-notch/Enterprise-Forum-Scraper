# -- coding: utf-8 --
import re
# import locale
import dateutil.parser as dparser

from .base_template import BaseTemplate

class VbiranParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "vbiran.ir"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'.*-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//li[contains(@id,"post_")]'
        self.header_xpath = '//li[contains(@id,"post_")]'
        self.date_xpath = './/span[@class="date"]//text()'
        self.title_xpath = '//span[contains(@class,"threadtitle")]//descendant::text()'
        self.post_text_xpath = './/div[contains(@class,"postbody")]//div[@class="content"]//descendant::text()[not(ancestor::div[@class="quote_container"])]'
        self.avatar_xpath = './/div[contains(@class,"userinfo")]//a[@class="postuseravatar"]//img/@src'
        self.comment_block_xpath = './/div[contains(@class,"posthead")]//span[@class="nodecontrols"]/a//text()'

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

    def get_author(self, tag):
        author = tag.xpath(
            './/a[contains(@class,"username")]//text()'
        )
        if not author:
            author = tag.xpath(
                './/span[contains(@class,"username")]//descendant::text()'
            )
        author = author[0].strip() if author else None
        return author

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)

        date_block = ' '.join(date_block)
        date = date_block.strip() if date_block else ""

        try:
            date = dparser.parse(date).timestamp()
            return str(date)
        except Exception:
            return ""
        return ""

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        comment_block = ''.join(comment_block)

        if comment_block:
            comment_id = comment_block.strip().split('#')[-1]



        return comment_id.replace(',', '').replace('.', '')
