# -- coding: utf-8 --
import datetime
import traceback

import dateutil.parser as dparser
import dateparser
import utils
import re

class BrokenPage(Exception):
    pass


class BaseTemplate:

    time_format = "%Y-%m-%d %H:%M:%S"

    def __init__(self, *args, **kwargs):
        self.start_date = kwargs.get("start_date")
        self.output_folder = kwargs.get('output_folder')
        self.folder_path = kwargs.get('folder_path')
        self.distinct_files = set()
        self.error_folder = f"{self.output_folder}/Errors"
        self.missing_header_folder = f"{self.output_folder}/Missing_Date&Author"      # path for backup template without Avatar, Date, Author
        self.missing_header_file_limit = 50
        self.checkonly = kwargs.get('checkonly')
        self.thread_id = None
        self.comment_pattern = None
        self.encoding = None
        self.mode = 'rb'
        self.offset_hours = 0
        self.comments_xpath = ''
        self.comment_block_xpath = ''
        self.author_xpath = ''
        self.post_text_xpath = ''
        self.protected_email_xpath = './/*[@class="__cf_email__"]/@data-cfemail'
        self.date_xpath = ''
        self.date_pattern = ''
        self.header_xpath = ''
        self.title_xpath = ''
        self.avatar_xpath = ''
        self.avatar_ext = ''
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.files = self.get_filtered_files(kwargs.get('files'))

        if self.start_date:
            try:
                self.start_date = datetime.datetime.strptime(
                    self.start_date,
                    self.time_format
                ).timestamp()
            except Exception as err:
                try:
                   self.start_date = datetime.datetime.strptime(
                        self.start_date,
                        "%Y-%m-%d"
                    ).timestamp()
                except Exception as err:
                    raise ValueError(
                        "Wrong date format. Correct format is: %s or %s." % (
                            self.time_format,
                            "%Y-%m-%d"
                        )
                    )

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: (int(self.thread_name_pattern.search(x).group(1)),
                           int(self.pagination_pattern.search(x).group(1))))

        return sorted_files

    def get_html_response(self, template, pattern=None, encoding=None, mode='rb'):
        return utils.get_html_response(template, pattern, encoding, mode)

    def get_pid(self):
        return self.thread_id

    def main(self):
        comments = []
        output_file = None

        for index, template in enumerate(self.files):
            print(template)
            try:
                html_response = self.get_html_response(template, self.comment_pattern, self.encoding, self.mode)
                file_name_only = template.split('/')[-1]
                match = self.thread_name_pattern.findall(file_name_only)

                if not match:
                    continue

                self.thread_id = match[0]

                pid = self.get_pid()

                pagination = None
                if getattr(self, 'pagination_pattern', None):
                    pagination = self.pagination_pattern.findall(file_name_only)
                    if pagination:
                        pagination = int(pagination[0])

                final = utils.is_file_final(
                    self.thread_id,
                    self.thread_name_pattern,
                    self.files,
                    index
                )

                if (
                    (pagination and pagination == 1) or
                    (self.thread_id not in self.distinct_files) and not output_file
                ):
                    self.distinct_files.add(self.thread_id)
                    # header data extract
                    data = self.header_data_extract(html_response, template)

                    if not data:
                        continue
                    # write file
                    output_file = '{}/{}.json'.format(
                        str(self.output_folder),
                        pid
                    )
                    file_pointer = open(output_file, 'w', encoding='utf-8')

                    error_msg = utils.write_json(file_pointer, data, self.start_date, self.checkonly)
                    if error_msg:
                        print(error_msg)
                        print('----------------------------------------\n')
                        if self.missing_header_file_limit > 0:
                            utils.handle_missing_header(
                                template,
                                self.missing_header_folder
                            )
                            self.missing_header_file_limit-=1
                        else:
                            print("----------------------------------\n")
                            print("Found 50 Files with missing header or date")
                            break
                        continue
                # extract comments
                extracted = self.extract_comments(html_response, pagination)
                comments.extend(extracted)

                # missing author and date check
                if self.checkonly:
                    error_msg = ""
                    for row in extracted:
                        if not row['_source'].get('author'):
                            error_msg = f'ERROR: Null Author Detected. pid={row["_source"]["pid"]};'
                            if row['_source'].get('cid'):
                                error_msg += f' cid={row["_source"]["cid"]};'
                        elif not row['_source'].get('date'):
                            error_msg = f'ERROR: Date not present. pid={row["_source"]["pid"]};'
                            if row['_source'].get('cid'):
                                error_msg += f' cid={row["_source"]["cid"]};'
                        if error_msg:
                            break
                    if error_msg:
                        print(error_msg)
                        print('----------------------------------------\n')
                        if self.missing_header_file_limit > 0:
                            utils.handle_missing_header(
                                template,
                                self.missing_header_folder
                            )
                            self.missing_header_file_limit-=1
                        else:
                            print("----------------------------------\n")
                            print("Found 50 Files with missing header or date")
                            break

                if final:
                    utils.write_comments(file_pointer, comments, output_file, self.start_date)
                    comments = []
                    output_file = None
                    final = None
                    if getattr(self, 'index', None):
                        self.index = 1

            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except Exception:
                traceback.print_exc()
                continue

    def header_data_extract(self, html_response, template):
        try:
            # ---------------extract header data ------------
            header = html_response.xpath(self.header_xpath)
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

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = "".join([t.strip() for t in title if t.strip()])

        return title

    def extract_comments(self, html_response, pagination=None):
        comments = list()
        comment_blocks = html_response.xpath(self.comments_xpath)

        if not self.comment_block_xpath:
            comment_blocks = comment_blocks[1:]\
                if pagination == 1 else comment_blocks

        for comment_block in comment_blocks:
            try:

                comment_id = self.get_comment_id(comment_block)
                if self.comment_block_xpath:
                    if not comment_id or comment_id == "1":
                        continue

                user = self.get_author(comment_block)
                comment_text = self.get_post_text(comment_block)
                comment_date = self.get_date(comment_block)

                pid = self.get_pid()
                avatar = self.get_avatar(comment_block)

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

    def get_comment_id(self, tag):
        comment_id = ""
        if self.comment_block_xpath:
            comment_block = tag.xpath(self.comment_block_xpath)
            comment_block = ''.join(comment_block).replace(',', '').replace('.', '')
        else:
            return str(self.index)

        if comment_block:
            comment_id = re.compile(r'(\d+)').findall(comment_block)[0]
            # comment_id = ''.join(comment_block).strip().split('#')[-1]

        return comment_id.replace(',', '').replace('.', '')


    def get_author(self, tag):
        author = tag.xpath(self.author_xpath)
        if author:
            author = ''.join(author).strip()
            return author
        else:
            return ''

    def get_post_text(self, tag):
        post_text_block = tag.xpath(self.post_text_xpath)
        if not post_text_block:
            return ''
        post_text = " ".join([
            post_text.strip() for post_text in post_text_block
        ])
        protected_email = tag.xpath(self.protected_email_xpath)
        if protected_email:
            decoded_values = [
                utils.get_decoded_email(e) for e in protected_email
            ]
            for decoded_value in decoded_values:
                post_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    post_text,
                    count=1
                )

        return post_text.strip()

    def parse_date_string(self, date_string):
        if not date_string:
            return ""

        try:
            date = datetime.datetime.strptime(date_string, self.date_pattern)
        except:
            try:  # check if date is already a timestamp
                date = float(date_string)
            except:
                err_msg = f"WARN: could not figure out date from: ({date_string}) using date pattern ({self.date_pattern})"
                print(err_msg)
                try:
                    date = dateparser.parse(date_string)
                except Exception as err3:
                    err_msg = f"ERROR: Parsing {date_string} date is failed. {err3}"
                    raise ValueError(err_msg)

        if isinstance(date, datetime.datetime):
            if self.offset_hours:
                date += datetime.timedelta(hours=self.offset_hours)
            date = date.timestamp()

        if date:
            curr_epoch = datetime.datetime.today().timestamp()
            if date > curr_epoch:
                err_msg = f"ERROR: the timestamp ({date}) is after current time ({curr_epoch})"
                print(err_msg)
                raise ValueError(err_msg)
            return str(date)
        return ""

    def get_date(self, tag):
        date_block = tag.xpath(self.date_xpath)
        date = date_block[0].strip() if date_block else None

        if not date:
            return ""

        # check if date is already a timestamp
        try:
            date = datetime.datetime.strptime(date, self.date_pattern).timestamp()
        except:
            try:
                date = float(date)
            except:
                err_msg = f"WARN: could not figure out date from: ({date}) using date pattern ({self.date_pattern})"
                print(err_msg)
                date = dateparser.parse(date).timestamp()
        if date:
            curr_epoch = datetime.datetime.today().timestamp()
            if date > curr_epoch:
                err_msg = f"ERROR: the timestamp ({date}) is after current time ({curr_epoch})"
                print(err_msg)
                raise RuntimeError(err_msg)
            return str(date)
        return ""

    def get_avatar(self, tag):
        avatar_block = tag.xpath(self.avatar_xpath)
        if not avatar_block:
            return ""

        if 'image/svg' in avatar_block[0]:
            return ""

        name_match = self.avatar_name_pattern.findall(avatar_block[0])
        if not name_match:
            return ""

        return f"{name_match[0]}.{self.avatar_ext}" if self.avatar_ext else name_match[0]


class MarketPlaceTemplate(BaseTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thread_name_pattern = re.compile(
            r'(\w+)\.html$'
        )
        self.files = self.get_filtered_files(kwargs.get('files'))

    def main(self):
        comments = []
        output_file = None
        for index, template in enumerate(self.files):
            try:
                html_response = utils.get_html_response(template)
                list_id = template.split('/')[-1].rsplit('.', 1)[0]
                # list_id = str(
                #     int.from_bytes(
                #         list_id.encode('utf-8'),
                #         byteorder='big'
                #     ) % (10 ** 7)
                # )
                self.process_page(list_id, html_response)
            except BrokenPage as ex:
                utils.handle_error(
                    pid,
                    self.error_folder,
                    ex
                )
            except Exception:
                traceback.print_exc()
                continue

    def process_page(self, list_id, html_response):
        data = {
            'marketplace': self.parser_name,
            'list_id': list_id
        }

        additional_data = self.extract_page_info(html_response)
        if not additional_data:
            return

        data.update(additional_data)
        final_data = {
            '_source': data
        }

        output_file = '{}/{}.json'.format(
            str(self.output_folder),
            list_id
        )

        with open(output_file, 'w', encoding='utf-8', newline='\r\n') as file_pointer:
            utils.write_json(file_pointer, final_data)
            print('\nJson written in {}'.format(output_file))
            print('----------------------------------------\n')


    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(x) is not None,
                files
            )
        )

        sorted_files = sorted(
            filtered_files,
            key=lambda x: self.thread_name_pattern.search(x).group(1))

        return sorted_files


    def extract_page_info(self, html_response):
        data = dict()

        list_name = self.get_list_name(html_response)
        list_description = self.get_list_description(html_response)
        vendor = self.get_vendor(html_response)

        data = {
            'list_name': list_name,
            'vendor': vendor,
            'description': list_description
        }

        return data

    def get_list_name(self, html_response):
        list_name = html_response.xpath(self.list_name_xpath)
        list_name = "".join([t.strip() for t in list_name if t.strip()])

        return list_name

    def get_vendor(self, html_response):
        vendor = html_response.xpath(self.vendor_xpath)
        if vendor:
            vendor = ''.join(vendor).strip()
            return vendor
        else:
            return ''

    def get_list_description(self, html_response):
        description_text_block = html_response.xpath(self.description_text_xpath)
        if not description_text_block:
            return ''
        description_text = " ".join([
            post_text.strip() for post_text in description_text_block
        ])
        protected_email = html_response.xpath(self.protected_email_xpath)
        if protected_email:
            decoded_values = [
                utils.get_decoded_email(e) for e in protected_email
            ]
            for decoded_value in decoded_values:
                description_text = re.sub(
                    r'\[email.*?protected\]',
                    decoded_value,
                    description_text,
                    count=1
                )

        return description_text.strip()