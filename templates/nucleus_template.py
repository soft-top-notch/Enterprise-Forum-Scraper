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


class NucleusParser:
    def __init__(self, parser_name, files, output_folder, folder_path):
        self.parser_name = "nucleus forum"
        self.output_folder = output_folder
        self.thread_name_pattern_1 = re.compile(r'viewtopic\.php\?pid=(\d+)')
        self.thread_name_pattern_2 = re.compile(r'viewtopic\.php\?id=(\d+)')
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
                lambda x: self.thread_name_pattern_1.search(x) is not None,
                files
            )
        )
        sorted_files_1 = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern_1.search(x).group(1)))

        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern_2.search(x) is not None,
                files
            )
        )
        sorted_files_2 = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern_2.search(x).group(1)))

        return sorted_files_1 + sorted_files_2

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            file_type = None
            try:
                html_response = utils.get_html_response(template)
                if html_response is None:
                    continue
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern_1.findall(file_name_only)
                if match:
                    file_type = 1
                else:
                    match = self.thread_name_pattern_2.findall(file_name_only)
                    if match:
                        file_type = 2
                if not file_type:
                    continue
                if file_type == 1:
                    pid = self.thread_id = match[0]
                else:
                    pid = self.thread_id = f'{match[0]}-1'
                print(template)
                if file_type == 1:
                    final = utils.is_file_final(
                        self.thread_id,
                        self.thread_name_pattern_1,
                        self.files,
                        index
                    )
                else:
                    final = utils.is_file_final(
                        match[0],
                        self.thread_name_pattern_2,
                        self.files,
                        index
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
          '//div[@id="brdmain"]/div[contains(@class,"blockpost")]'
        )
        for comment_block in comment_blocks:
            user = self.get_author(comment_block)
            comment_id = self.get_comment_id(comment_block)
            if not comment_id or comment_id == "1":
                continue
            comment_text = self.get_post_text(comment_block)
            comment_date = self.get_date(comment_block)
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
            comments.append({
                
                '_source': source,
            })
        return comments

    def header_data_extract(self, html_response, template):
        try:

            # ---------------extract header data ------------
            header = html_response.xpath(
                '//div[@id="brdmain"]/div[contains(@class,"blockpost")]'
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
            return {
                
                '_source': source
            }
        except:
            ex = traceback.format_exc()
            raise BrokenPage(ex)

    def get_date(self, tag):
        date_block = tag.xpath(
            'h2//span[@class="conr"]/'
            'following-sibling::a[1]/text()'
        )
        date = date_block[0].strip() if date_block else ""

        try:
            pattern = "%Y-%m-%d %H:%M:%S"
            date = datetime.datetime.strptime(date, pattern).timestamp()
            return str(date)
        except:
            return ""

    def get_author(self, tag):
        author = tag.xpath(
            'div//dt/strong/a/text()'
        )
        if not author:
            author = tag.xpath(
                'div//dt/strong/text()'
            )
        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(
            'div//div[@class="postright"]/h3/text()'
        )
        title = title[0].strip() if title else None
        return title

    def get_post_text(self, tag):
        post_text = tag.xpath(
            'div//div[@class="postmsg"]/*/text()'
        )

        post_text = "\n".join(
            [text.strip() for text in post_text if text.strip()]
        ) if post_text else ""
        return post_text.strip()

    def get_comment_id(self, tag):
        comment_block = tag.xpath(
            'h2//span[@class="conr"]/text()'
        )
        if comment_block:
            commentID = comment_block[0].split('#')[-1].replace(',', '')
            return commentID.replace(',', '')
        return ""
