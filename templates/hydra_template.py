# -- coding: utf-8 --
import os
import re
import traceback
import json
import utils
import datetime
from lxml.html import fromstring


class BrokenPage(Exception):
    pass


class HydraParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = parser_name
        self.output_folder = output_folder
        self.thread_name_pattern = re.compile(r'viewtopic\.php.*p=(\d+)')
        self.files = self.get_filtered_files(files)
        self.folder_path = folder_path
        self.distinct_files = set()
        self.error_folder = "{}/Errors".format(output_folder)
        self.thread_id = None
        # main function
        self.main()

    def get_pid(self):
        pid_pattern = re.compile(r'p=(\d+)')
        pid = pid_pattern.findall(self.thread_id)
        pid = pid[0] if pid else self.thread_id
        return pid

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        pid_pattern = re.compile(r'p=(\d+)')
        sorted_files = sorted(
            filtered_files,
            key=lambda x: int(pid_pattern.search(x).group(1)))

        return sorted_files

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
                self.thread_id = match[0]
                pid = self.get_pid()
                final = utils.is_file_final(
                    self.thread_id, self.thread_name_pattern, self.files, index
                )
                if self.thread_id not in self.distinct_files and\
                   not output_file:

                    # header data extract
                    data = self.header_data_extract(html_response, template)
                    if not data:
                        comments.extend(self.extract_comments(html_response))
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
                comments.extend(self.extract_comments(html_response))

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
          '//div[@id="page-body"]/div[contains(@class, "post bg")]'
        )
        for index, comment_block in enumerate(comment_blocks[1:], 1):
            user = self.get_author(comment_block)
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
            pid = self.get_pid()
            comments.append({
                
                '_source': {
                    'pid': pid,
                    'date': comment_date,
                    'message': comment_text.strip(),
                    'cid': str(index),
                    'author': user,
                },
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[@id="page-body"]/div[contains(@class, "post bg")]'
            )
            if not header:
                return
            # if not self.get_comment_id(header[0]) == "1":
            #     return
            title = self.get_title(html_response)
            date = self.get_date(header[0])
            author = self.get_author(header[0])
            post_text = self.get_post_text(header[0])
            pid = self.get_pid()
            return {
                
                '_source': {
                    'pid': pid,
                    's': title,
                    'd': date,
                    'a': author,
                    'm': post_text.strip(),
                }
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_date(self, tag):
        date = tag.xpath(
            'div//p[@class="author"]/text()'
        )
        date_pattern = re.compile(r'\s+([SMTWF].*[aApP][mM])')
        match = date_pattern.findall(date[-1])
        date = match[0].strip() if match else None
        try:
            pattern = '%a %b %d, %Y %I:%M  %p'
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            traceback.print_exc()
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div//p[@class="author"]/strong/a/text()'
        )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            '//div[@id="page-body"]/h2/a/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'div//div[@class="content"]/text()'
        )

        post_text = "\n".join(
            [text.strip() for text in post_text if text.strip()]
        ) if post_text else ""
        return post_text.strip()
