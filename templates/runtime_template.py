# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class RuntimeParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "runtime.rip"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//article[contains(@class,"post-article")]'
        self.header_xpath = '//article[contains(@class,"post-article")]'
        self.date_xpath = 'div//span[contains(@class, "post_date")]/text()'
        self.date_pattern = '%m-%d-%Y, %I:%M %p'
        self.author_xpath = 'div//div[contains(@class,"post-username")]/a/text()'
        self.title_xpath = '//div[@class="thread-header"]/h1/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div//div[@class="right postbit-number"]/strong/a/text()'

        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if not author:
            author = tag.xpath(
                'div//div[contains(@class,"post-username")]/a/span/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)
        if comment_block:
            comment_id = comment_block[-1].strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')
