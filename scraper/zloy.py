import re
import os
import uuid

from datetime import datetime, timedelta

from scrapy import (
    Request,
    FormRequest,
    Selector
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


REQUEST_DELAY = 0.5
NO_OF_THREADS = 5


class ZloySpider(SitemapSpider):

    name = "zloy_spider"

    # Url stuffs
    base_url = "https://forum.zloy.bz/"

    # Xpath stuffs
    forum_xpath = '//a[contains(@href, "forumdisplay.php?")]/@href'
    thread_xpath = '//tr[td[contains(@id, "td_threadtitle_")]]'
    thread_first_page_xpath = '//td[contains(@id, "td_threadtitle_")]/div'\
                              '/a[contains(@href, "showthread.php?")]/@href'
    thread_last_page_xpath = '//td[contains(@id, "td_threadtitle_")]/div/span'\
                             '/a[contains(@href, "showthread.php?")]'\
                             '[last()]/@href'
    thread_date_xpath = '//span[@class="time"]/preceding-sibling::text()'

    pagination_xpath = '//a[@rel="next"]/@href'
    thread_pagination_xpath = '//a[@rel="prev"]/@href'
    thread_page_xpath = '//div[@class="pagenav"]//span/strong/text()'
    post_date_xpath = '//table[contains(@id, "post")]//td[@class="thead"][1]'\
                      '/a[contains(@name,"post")]'\
                      '/following-sibling::text()[1]'
    avatar_xpath = '//a[contains(@href, "member.php?") and img/@src]'

    # Regex stuffs
    topic_pattern = re.compile(
        r"t=(\d+)",
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r"u=(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = False
    download_delay = REQUEST_DELAY
    download_thread = NO_OF_THREADS
    post_datetime_format = '%d.%m.%Y'
    sitemap_datetime_format = '%d.%m.%Y'
    cloudfare_delay = 10

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        thread_date = thread_date.strip()
        if "днес" in thread_date.lower():
            return datetime.today()
        elif "вчера" in thread_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                thread_date,
                self.sitemap_datetime_format
            )

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        # Standardize thread_date
        post_date = post_date.split(',')[0].strip()
        if not post_date:
            return

        if "днес" in post_date.lower():
            return datetime.today()
        elif "вчера" in post_date.lower():
            return datetime.today() - timedelta(days=1)
        else:
            return datetime.strptime(
                post_date,
                self.post_datetime_format
            )

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex
            }
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = response.xpath(self.forum_xpath).extract()
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url
            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                dont_filter=True,
                meta=self.synchronize_meta(response)
            )

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from self.parse_avatars(response)

    def parse_avatars(self, response):

        # Synchronize headers user agent with cloudfare middleware
        self.synchronize_headers(response)

        # Save avatar content
        for avatar in response.xpath(self.avatar_xpath):
            avatar_url = avatar.xpath('img/@src').extract_first()

            # Standardize avatar url
            if not avatar_url.lower().startswith("http"):
                avatar_url = self.base_url + avatar_url

            if 'image/svg' in avatar_url:
                continue

            user_url = avatar.xpath('@href').extract_first()
            match = self.avatar_name_pattern.findall(user_url)
            if not match:
                continue

            file_name = os.path.join(
                self.avatar_path,
                f'{match[0]}.jpg'
            )

            if os.path.exists(file_name):
                continue

            yield Request(
                url=avatar_url,
                headers=self.headers,
                callback=self.parse_avatar,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "file_name": file_name
                    }
                ),
            )


class ZloyScrapper(SiteMapScrapper):

    spider_class = ZloySpider
    site_name = 'forum.zloy.bz'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
