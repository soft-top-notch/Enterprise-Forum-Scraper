# -- coding: utf-8 --
import re
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class MfdParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "forum.mfd.ru"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.index = 1
        self.mode = 'r'
        self.comments_xpath = '//div[@class="mfd-post"]'
        self.header_xpath = '//div[@class="mfd-post"]'
        self.date_pattern = "%d.%m.%Y %H:%M"
        self.date_xpath = './/div[@class="mfd-post-top-1"]/a/text()'
        self.author_xpath = './/div[@class="mfd-post-top-0"]//text()'
        self.title_xpath = '//div[@class="mfd-header"]/h1/text()'
        self.post_text_xpath = './/div[@class="mfd-quote-text"]//text()'
        self.avatar_xpath = './/div[@class="mfd-post-avatar"]//img/@src'

        self.offset_hours = -3

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
        date = date_block[0].strip() if date_block else None
        result = ""

        # check if date is already a timestamp
        try:
            date = datetime.datetime.strptime(date, self.date_pattern)
        except Exception as err1:
            print(f"WARN: could not figure out date from: ({date}) using date pattern ({self.date_pattern})")

            try:
                result = float(date)
            except Exception as err2:
                try:
                    date = dparser.parse(date, dayfirst=True)
                except Exception as err3:
                    err_msg = f"ERROR: Parsing {date} date is failed. {err3}"
                    raise ValueError(err_msg)

        if isinstance(date, datetime.datetime):
            if self.offset_hours:
                date += datetime.timedelta(hours=self.offset_hours)
            result = str(date.timestamp())

        return result

    def extract_comments(self, html_response, pagination):
        comments = []
        comment_blocks = html_response.xpath(self.comments_xpath)
        comment_blocks = comment_blocks[1:] if pagination == 1 else comment_blocks

        for comment_block in comment_blocks:
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            avatar = self.get_avatar(comment_block)
            pid = self.thread_id

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': str(self.index),
                'author': user,
            }
            if comment_date:
                source.update({
                    'date': comment_date
                })
            if avatar:
                source.update({
                    'img': avatar
                })
            comments.append({
                '_source': source,
            })
            self.index += 1

        return comments

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[0].strip().split(']')[-1] if title else None

        return title

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        if name_match[0].startswith('svg'):
            return ""

        return name_match[0]
