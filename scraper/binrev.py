import re
import uuid

from scrapy import (
    Request,
    FormRequest
)

from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)

USERNAME = "vrx9"
PASSWORD = "4hr63yh38a"


class BinRevSpider(SitemapSpider):
    name = 'binrev_spider'
    base_url = "http://www.binrev.com/"

    # xpaths
    login_form_xpath = '//form[@method="post"]'
    forum_xpath = '//div[@class="ipsDataItem_main"]//h4/a/@href|'\
                  '//div[@class="ipsDataItem_main"]/ul/li'\
                  '/a[contains(@href, "forum/")]/@href'

    pagination_xpath = '//li[@class="ipsPagination_next"]/a/@href'

    thread_xpath = '//li[contains(@class, "ipsDataItem ")]'
    thread_first_page_xpath = './/div[@class="ipsType_break ipsContained"]'\
                              '/a/@href'
    thread_last_page_xpath = './/li[@class="ipsPagination_page"][last()]'\
                             '/a/@href'

    thread_date_xpath = './/li[@class="ipsType_light"]/a/time/@datetime'
    thread_page_xpath = '//li[contains(@class, "ipsPagination_active")]'\
                        '/a/text()'
    thread_pagination_xpath = '//li[@class="ipsPagination_prev"]'\
                              '/a/@href'

    post_date_xpath = '//a/time[@datetime]/@datetime'

    avatar_xpath = '//li[@class="cAuthorPane_photo"]/a/img/@src'

    # Regex stuffs
    topic_pattern = re.compile(
        r'topic/(\d+)-',
        re.IGNORECASE
    )
    avatar_name_pattern = re.compile(
        r'.*/(\S+\.\w+)',
        re.IGNORECASE
    )

    # Login Failed Message
    login_failed_xpath = '//p[contains(@class, "ipsMessage ipsMessage_error")]'

    # Other settings
    use_proxy = "VIP"
    sitemap_datetime_format = '%Y-%m-%dT%H:%M:%SZ'
    post_datetime_format = '%Y-%m-%dT%H:%M:%SZ'

    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "cookiejar": uuid.uuid1().hex,
                "country": "us"
            },
            callback=self.parse,
            dont_filter=True,
            errback=self.parse_failure
        )

    def parse_failure(self, failure):
        yield from self.start_requests()

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        yield FormRequest.from_response(
            response,
            formxpath=self.login_form_xpath,
            formdata={
                "auth": USERNAME,
                "password": PASSWORD,
            },
            meta=self.synchronize_meta(
                response,
                default_meta={
                    "country": "us"
                }
            ),
            dont_filter=True,
            headers=self.headers,
            callback=self.parse_start
        )

    def parse_start(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        # Check if login failed
        self.check_if_logged_in(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
        for forum_url in all_forums:

            # Standardize url
            if self.base_url not in forum_url:
                forum_url = self.base_url + forum_url

            yield Request(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(
                    response,
                    default_meta={
                        "country": "us"
                    }
                )
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)

        # Parse generic avatar
        yield from super().parse_avatars(response)


class BinRevScrapper(SiteMapScrapper):

    spider_class = BinRevSpider
    site_name = 'binrev.com'
    site_type = 'forum'
