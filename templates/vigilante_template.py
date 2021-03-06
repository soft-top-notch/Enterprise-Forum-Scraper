# -- coding: utf-8 --
import re
# import locale
import datetime
import dateutil.parser as dparser

from .base_template import BaseTemplate


class VigilanteParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "vigilante.tech"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.header_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.date_xpath = '..//span[@class="post_date"]/text()'
        self.title_xpath = '//td[@class="thead"]/div/strong/text()'
        self.post_text_xpath = './/div[@class="post_body scaleimages"]'\
                               '/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = '..//div[@class="post_head"]/div/'\
                                   'strong/a/text()'
        self.author_xpath = './/div[@class="author_information"]'\
                            '//strong[1]//text()'

        # main function
        self.main()

    def extract_comments(self, html_response, pagination):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        for index, comment_block in enumerate(comment_blocks, 1):
            comment_id = self.get_comment_id(comment_block, index)
            if not comment_id or comment_id == "1":
                continue

            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block, index)
            avatar = self.get_avatar(comment_block)
            pid = self.thread_id

            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': comment_id,
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

        return comments

    def get_date(self, tag, index=1):
        date_block = tag.xpath(self.date_xpath)[index - 1]
        date = date_block.strip() if date_block else ""
        try:
            pattern = "%m-%d-%Y, %I:%M %p"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except Exception:
            try:
                date = dparser.parse(date).timestamp()
                return str(date)
            except Exception:
                pass

            return ""

    def get_comment_id(self, tag, index=1):
        comment_id = ""
        comment_block = tag.xpath(self.comment_block_xpath)[index-1]

        if comment_block:
            comment_id = comment_block.split('#')[-1]

        return comment_id.replace(',', '')
