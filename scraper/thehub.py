import re
import os
import time
import traceback
import requests
from requests import Session
from scraper.base_scrapper import BaseScrapper

PROXY = "socks5h://localhost:9050"
USERNAME = "vrx9"
PASSWORD = "Night#Hub998"


class TheHubScrapper(BaseScrapper):
    def __init__(self, kwargs):
        super(TheHubScrapper, self).__init__(kwargs)
        self.base_url = 'http://thehub7xbw4dc5r2.onion/index.php'
        self.topic_pattern = re.compile(r'topic=(\d+)')
        self.username = kwargs.get('user')
        self.password = kwargs.get('password')
        self.comment_pattern = re.compile(r'(\<\!--.*?--\!\>)')
        self.proxy = kwargs.get('proxy') or PROXY
        self.cloudfare_error = None

    def get_page_content(self, url):
        time.sleep(self.wait_time)
        try:
            response = self.session.get(url)
            content = response.content
            html_response = self.get_html_response(content)
            if html_response.xpath('//div[@class="errorwrap"]'):
                return
            return content
        except:
            traceback.print_exc()
            return

    def save_avatar(self, name, url):
        avatar_file = f'{self.avatar_path}/{name}'
        if os.path.exists(avatar_file):
            return
        content = self.get_page_content(url)
        if not content:
            return
        if 'Attachment Not Found' in str(content):
            return
        with open(avatar_file, 'wb') as f:
            f.write(content)

    def process_first_page(self, topic_url):
        topic = self.topic_pattern.findall(topic_url)
        if not topic:
            return
        topic = topic[0]
        initial_file = f'{self.output_path}/{topic}-1.html'
        if os.path.exists(initial_file):
            return
        content = self.get_page_content(topic_url)
        if not content:
            print(f'No data for url: {topic_url}')
            return
        with open(initial_file, 'wb') as f:
            f.write(content)
        print(f'{topic}-1 done..!')
        content = self.comment_pattern.sub('', str(content))
        html_response = self.get_html_response(content)
        if html_response.xpath(
            '//font[contains(text(), "Verifying your browser, please wait")]'
        ):
            print('DDOS identified. Retyring after a min')
            time.sleep(60)
            return self.process_first_page(topic_url)
        avatar_info = self.get_avatar_info(html_response)
        for name, url in avatar_info.items():
            self.save_avatar(name, url)
        return html_response

    def process_topic(self, topic_url):
        html_response = self.process_first_page(topic_url)
        if html_response is None:
            return
        while True:
            response = self.write_paginated_data(html_response)
            if response is None:
                return
            topic_url, html_response = response

    def write_paginated_data(self, html_response):
        next_page_block = html_response.xpath(
            '//div[@class="pagelinks floatleft"]/strong'
            '/following-sibling::a[1]/@href'
        )
        if not next_page_block:
            return
        next_page_url = next_page_block[0]
        next_page_url = self.base_url + next_page_url\
            if not next_page_url.startswith('http') else next_page_url
        pattern = re.compile(r'topic=(\d+)\.(\d+)')
        match = pattern.findall(next_page_url)
        if not match:
            return
        topic, pagination_value = match[0]
        pagination_value = int(int(pagination_value)/20 + 1)
        content = self.get_page_content(next_page_url)
        if not content:
            return
        paginated_file = f'{self.output_path}/{topic}-{pagination_value}.html'
        with open(paginated_file, 'wb') as f:
            f.write(content)

        print(f'{topic}-{pagination_value} done..!')
        content = self.comment_pattern.sub('', str(content))
        html_response = self.get_html_response(content)
        avatar_info = self.get_avatar_info(html_response)
        for name, url in avatar_info.items():
            self.save_avatar(name, url)
        return next_page_url, html_response

    def process_forum(self, url):
        while True:
            print(f"Forum URL: {url}")
            forum_content = self.get_page_content(url)
            if not forum_content:
                print(f'No data for url: {forum_content}')
                return
            forum_content = self.comment_pattern.sub('', str(forum_content))
            html_response = self.get_html_response(forum_content)
            topic_urls = html_response.xpath(
                '//td[contains(@class, "subject ")]'
                '//span[contains(@id, "msg_")]'
                '/a/@href'
            )
            # print(len(topic_urls))
            for topic_url in topic_urls:
                topic_url = self.base_url + topic_url\
                    if not topic_url.startswith('http') else topic_url
                self.process_topic(topic_url)
            forum_pagination_url = html_response.xpath(
                '//div[@class="pagelinks floatleft"]/strong'
                '/following-sibling::a[1]/@href'
            )
            if not forum_pagination_url:
                return
            url = forum_pagination_url[0]
            url = self.base_url + url\
                if not url.startswith('http') else url

    def get_forum_urls(self, html_response):
        urls = set()
        extracted_urls = html_response.xpath(
            '//td[@class="info"]/a[@class="subject"]/@href'
        )
        return extracted_urls

    def clear_cookies(self,):
        self.session.cookies.clear()

    def get_avatar_info(self, html_response):
        avatar_info = dict()
        urls = html_response.xpath(
            '//li[@class="avatar"]/a/img/@src'
        )
        for url in urls:
            url = self.base_url + url\
                if not url.startswith('http') else url
            avatar_name_pattern = re.compile(r'attach=(\d+)')
            name_match = avatar_name_pattern.findall(url)
            if not name_match:
                continue
            name = f'{name_match[0]}.jpg'

            if name not in avatar_info:
                avatar_info.update({
                    name: url
                })
        return avatar_info

    def login(self):
        password = self.password or PASSWORD
        username = self.username or USERNAME
        response = self.session.get(self.base_url).content
        if not response:
            return
        html_response = self.get_html_response(response)
        token = html_response.xpath(
            '//p[@class="centertext smalltext"]/'
            'following-sibling::input[1]'
        )
        if not token:
            return
        token_key = token[0].xpath('@name')[0]
        token_value = token[0].xpath('@value')[0]
        form_data = {
            "cookieneverexp": "on",
            "hash_passwrd": "",
            "passwrd": "Night#Hub998",
            "user": "vrx9",
            token_key: token_value,
        }
        params = {
            'action': 'login2'
        }
        login_response = self.session.post(
            self.base_url,
            params=params,
            data=form_data
        )
        html_response = self.get_html_response(login_response.content)
        if html_response.xpath(
           '//span[text()="Incorrect username and/or password."]'):
            return
        return html_response

    def do_scrape(self):
        print('************  TheHubScrapper  Started  ************\n')
        self.session.proxies.update({
            'http': self.proxy,
            'https': self.proxy,
        })
        html_response = self.login()
        if html_response is None:
            print('Login failed! Exiting...')
            return
        print('Login Successful!')
        forum_urls = self.get_forum_urls(html_response)
        print(forum_urls)
        # return
        # forum_urls = ['http://carder.me/forumdisplay.php?f=8']
        for forum_url in forum_urls:
            self.process_forum(forum_url)


def main():
    template = TheHubScrapper()
    template.do_scrape()


if __name__ == '__main__':
    main()