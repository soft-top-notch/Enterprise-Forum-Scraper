# -- coding: utf-8 --
import os
import re
from collections import OrderedDict
import traceback
import json
import utils
import datetime
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class HellParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = "hell forum"
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(
            r'index\.php(?!action).*topic(\d+).*html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
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

    def get_pid(self, html_response):
        header = html_response.xpath(
          '//div[@class="post_wrapper"]'
        )
        if not header:
            print('no header')
            return
        pid_block = header[0].xpath('div[@class="postarea"]//h5/a/@href')
        if not pid_block:
            return
        pid_pattern = re.compile(r'topic=(\d+)')
        pid_match = pid_pattern.findall(pid_block[0])
        pid = pid_match[0] if pid_match else None
        return pid

    def main(self):
        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = utils.get_html_response(template)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)
                if not match:
                    continue
                pid = self.thread_id = self.get_pid(html_response)
                if not pid:
                    continue
                output_file = '{}/{}.json'.format(
                    str(self.output_folder),
                    pid
                )
                with open(output_file, 'a', encoding='utf-8') as f:
                    if self.thread_id not in self.distinct_files:

                        # header data extract
                        data = self.header_data_extract(
                            html_response, template)
                        if not data:
                            comments = self.extract_comments(html_response)
                            utils.write_comments(f, comments, output_file)
                            continue
                        self.distinct_files.add(self.thread_id)
                        utils.write_json(f, data)
                        comments = self.extract_comments(html_response)
                        utils.write_comments(f, comments, output_file)
                    # else:
                    #     # extract comments
                    #     comments = self.extract_comments(html_response)
                    #     utils.write_comments(f, comments, output_file)
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
          '//div[@class="post_wrapper"]'
        )
        # print(comment_blocks)
        for index, comment_block in enumerate(comment_blocks[1:], 1):
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.thread_id
            avatar = self.get_avatar(comment_block)
            source = {
                'forum': self.parser_name,
                'pid': pid,
                'message': comment_text.strip(),
                'cid': str(index),
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

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[@class="post_wrapper"]'
            )
            if not header:
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
        date = tag.xpath(
            'div//div[@class="smalltext"]/text()'
        )
        if not date:
            return ""
        date_pattern = re.compile(r'(.*[aApP][mM])')
        match = date_pattern.findall(date[-1])
        date = match[0].strip() if match else ""
        if not date:
            return ""
        try:
            pattern = "%B %d, %Y, %I:%M:%S %p"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div[@class="poster"]'
            '/h4/a/text()'
        )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            'div//h5/a/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text_block = tag.xpath(
            'div//div[@class="post"]/'
            '/div[@class="inner"]'
        )
        post_text = "\n".join([
            post_text.xpath('string()') for post_text in post_text_block
        ])
        return post_text.strip()

    def get_avatar(self, tag):
        avatar_block = tag.xpath(
            'div//img[@class="avatar"]/@src'
        )
        if not avatar_block:
            return ""
        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""
        return name_match[0]

    def get_comment_id(self, tag):
        comment_id = ""
        comment_block = tag.xpath(
            'div[@class="postarea"]'
            '//div[@class="smalltext"]/strong/text()'
        )
        if comment_block:
            comment_pattern = re.compile(r'Reply #(\d+) on:')
            match = comment_pattern.findall(comment_block[0])
            comment_id = match[0] if match else ""

        return comment_id.replace(',', '')
