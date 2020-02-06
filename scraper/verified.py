import os
import re
import scrapy
from math import ceil
import configparser
from scrapy import (
    Request,
    FormRequest
)

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 1
NO_OF_THREADS = 1

USERNAME = "cyrax11"
MD5PASS = "5d22b48847fe3b55982c52f75a34c9a3"
PASSWORD = "Night#Verify098"


class VerifiedScSpider(SitemapSpider):

    name = 'verifiedsc_spider'

    # Url stuffs
    base_url = "https://verified.sc/"

    # Css stuffs
    login_css_form = "form[action*=login]"

    # Xpath stuffs
    
    # Regex stuffs
    topic_pattern = re.compile(
        r".*t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r"&page=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False

    def parse(self, response):

        # Synchronize user agent in cloudfare middleware
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formcss=self.login_css_form,
            formdata={
                "vb_login_username": USERNAME,
                "vb_login_password": "",
                "vb_login_md5password": MD5PASS,
                "vb_login_md5password_utf": MD5PASS,
                "cookieuser": None,
                "s": "",
                "url": "/",
                "do": "login"
            },
            meta=self.synchronize_meta(response),
            dont_filter=True,
            callback=self.parse_login
        )

    def parse_login(self, response):
        forums = response.xpath(
            '//a[contains(@href, "forumdisplay.php?f=")]')
        for forum in forums:
            url = forum.xpath('@href').extract_first()
            if self.base_url not in url:
                url = self.base_url + url.strip('.')
            yield Request(
                url=url,
                callback=self.parse_forum,
                headers=self.headers,
                meta={'proxy': self.proxy}
            )

        # Test for single Forum
        # url = 'http://verified2ebdpvms.onion/forumdisplay.php?f=77'
        # yield Request(
        #     url=url,
        #     callback=self.parse_forum,
        #     headers=self.headers,
        #     meta={'proxy': self.proxy}
        # )

    def parse_forum(self, response):
        print('next_page_url: {}'.format(response.url))
        threads = response.xpath(
            '//a[contains(@id, "thread_title_")]')
        for thread in threads:
            thread_url = thread.xpath('@href').extract_first()
            if self.base_url not in thread_url:
                thread_url = self.base_url + thread_url
            topic_id = self.topic_pattern.findall(thread_url)
            if not topic_id:
                continue
            file_name = '{}/{}-1.html'.format(self.output_path, topic_id[0])
            if os.path.exists(file_name):
                continue
            yield Request(
                url=thread_url,
                callback=self.parse_thread,
                headers=self.headers,
                meta={'topic_id': topic_id[0], 'proxy': self.proxy}
            )

        next_page = response.xpath('//a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                callback=self.parse_forum,
                headers=self.headers,
                meta={'proxy': self.proxy}
            )

    def parse_thread(self, response):
        topic_id = response.meta['topic_id']
        pagination = self.pagination_pattern.findall(response.url)
        if pagination:
            paginated_value = int(pagination[0])
        else:
            paginated_value = 1
        file_name = '{}/{}-{}.html'.format(
            self.output_path, topic_id, paginated_value)
        with open(file_name, 'wb') as f:
            f.write(response.text.encode('utf-8'))
            print(f'{topic_id}-{paginated_value} done..!')

        next_page = response.xpath('//a[@rel="next"]')
        if next_page:
            next_page_url = next_page.xpath('@href').extract_first()
            if self.base_url not in next_page_url:
                next_page_url = self.base_url + next_page_url.strip('.')
            yield Request(
                url=next_page_url,
                callback=self.parse_thread,
                headers=self.headers,
                meta={'topic_id': topic_id, 'proxy': self.proxy}
            )


class VerifiedScScrapper(SiteMapScrapper):

    spider_class = VerifiedScSpider

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                'DOWNLOAD_DELAY': REQUEST_DELAY,
                'CONCURRENT_REQUESTS': NO_OF_THREADS,
                'CONCURRENT_REQUESTS_PER_DOMAIN': NO_OF_THREADS,
            }
        )
        return settings


if __name__ == "__main__":
    pass
