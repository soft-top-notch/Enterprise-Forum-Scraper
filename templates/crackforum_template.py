# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
# import locale
import json
import utils
import datetime
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class CrackForumParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "crack-forum.ru"
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.distinct_files = set()
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_id = None
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
            key=lambda x: int(self.thread_name_pattern.search(x).group(1)))

        return sorted_files

    def get_pid(self, topic):
        return str(abs(hash(topic)) % (10 ** 6))

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue
                pid = self.thread_id = match[0]
                pagination = self.pagination_pattern.findall(file_name_only)
                if pagination:
                    pagination = int(pagination[0])
                final = utils.is_file_final(
                    self.thread_id,
                    self.thread_name_pattern,
                    self.files,
                    index
                )
                if self.thread_id not in self.distinct_files and\
                   not output_file:

                    # header data extract
                    data = self.header_data_extract(
                        html_response, template)
                    if not data or not pagination == 1:
                        comments.extend(
                            self.extract_comments(html_response))
                        continue
                    self.distinct_files.add(self.thread_id)

                    # write file
                    output_file = '{}/{}.json'.format(
                        str(self.output_folder),
                        pid
                    )
                    file_pointer = open(output_file, 'w', encoding='utf-8')
                    utils.write_json(file_pointer, data)
                # extract comments
                comments.extend(
                    self.extract_comments(html_response))

                if final:
                    utils.write_comments(file_pointer, comments, output_file)
                    comments = []
                    output_file = None
            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except:
                traceback.print_exc()
                continue

    def extract_comments(self, html_response):
        comments = list()
        comment_blocks = html_response.xpath(
          '//div[contains(@id, "posts")]/div[contains(@align,"center")]'
        )

        for index, comment_block in enumerate(comment_blocks, 1):
            try:
                user = self.get_author(comment_block)
                comment_text = self.get_post_text(comment_block)
                comment_date = self.get_date(comment_block)
                pid = self.thread_id
                avatar = self.get_avatar(comment_block)
                comment_id = self.get_comment_id(comment_block)
                if not comment_id or comment_id == "1":
                    continue
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
            except:
                continue
        return comments

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
          '//div[contains(@id, "posts")]/div[contains(@align,"center")]'
            )
            if not header:
                return
            if not self.get_comment_id(header[0]) == "1":
                return
            title = self.get_title(header[0])
            date = self.get_date(header[0])
            author = self.get_author(header[0])
            post_text = self.get_post_text(header[0])
            pid = self.thread_id
            avatar = self.get_avatar(header[0])
            source = {
                'forum': self.parser_name,
                'pid': pid,
                'subject': title,
                'author': author,
                'message': post_text.strip(),
            }
            if date:
                source.update({
                   'date': date
                })
            if avatar:
                source.update({
                    'img': avatar
                })
            return {
                '_source': source
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_date(self, tag):
        date = ""
        date_block = tag.xpath(
            './/table[contains(@class, "tborder")][1]//td[contains(@class, "thead")][1]/text()'
        )
        date_block = "".join(date_block)
        if date_block:
            date = date_block[0].strip()
        if not date:
            return ""
        try:
            pattern = "%d.%m.%Y, %H:%M"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            './/table//a[contains(@class,"username")]//text()'
        )
        if not author:
            author = tag.xpath(
                './/table//div[contains(@id, "postmenu_")]/text()'
            )
    
        if not author:
            author = tag.xpath(
                './/table//a[@class="bigusername"]/span/b/text()'
            )
    
        if not author:
            author = tag.xpath(
                './/a[@class="bigusername"]/font/strike/text()'
            )

        author = ''.join(author)        

        author = author.strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//table[1]//tr/td[1]//tr[2]/td/strong/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            './/div[contains(@id, "post_message")]/text()'
        )
        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])
        return post_text.strip()

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            './/table[contains(@id, "post")]//tr[2]/td[1]//img/@src'
        )
        if not avatar_block:
            return ""
        if "image.php" in avatar_block[0]:
            avatar_name_pattern = re.compile(r'u=(\d+)')
            name_match = avatar_name_pattern.findall(avatar_block[0])
            if name_match:
                name = f'{name_match[0]}.jpg'
                return name
        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""
        return name_match[0]

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(
            './/table//td[2][@class="thead"]//a//text()'
        )
        # print(comment_block)
        if comment_block:
            comment_id = comment_block[0].strip().split('#')[-1]
        return comment_id.replace(',', '').replace('.', '')