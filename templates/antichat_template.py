# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime
from lxml.html import fromstring


from .base_template import BaseTemplate


class AntichatParser(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "antichat.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//ol[@class="messageList"]/li'
        self.header_xpath = '//ol[@class="messageList"]/li'
        self.date_xpath = '//div[@class="privateControls"]'\
                      '//span[@class="DateTime"]/@title|'\
                      '//div[@class="privateControls"]'\
                      '//abbr[@class="DateTime"]/@data-datestring'
        self.date_pattern = '%d %b  %Y'
        self.author_xpath = 'div//div[@class="uix_userTextInner"]/a[@class="username"]//text()'
        self.title_xpath = '//div[@class="titleBar"]/h1/text()'
        self.post_text_xpath = 'div//blockquote[contains(@class,"messageText")]//text()'
        self.comment_block_xpath = 'div//div[@class="messageDetails"]/a/text()'
        self.avatar_xpath = 'div//div[@class="uix_avatarHolderInner"]/a/img/@src'
        self.moderator_avartar_xpath = 'div//div[@class="uix_avatarHolderInner"]/a[contains(@href,"members/1/")]'
        # main function
        self.main()

    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if author:
            author = ''.join(author).strip()
            return author
        else:
            moderator_avartar = tag.xpath(self.moderator_avartar_xpath)
            if moderator_avartar:
                return 'moderator'
            else:
                return ''
