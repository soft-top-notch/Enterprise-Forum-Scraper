import os
import re

from scrapy.http import Request
from scrapy.exceptions import CloseSpider
from datetime import datetime
import dateparser

from .base_scrapper import SitemapSpider, SiteMapScrapper


class OffensiveCommunitySpider(SitemapSpider):
    name = 'offensive_community_spider'
    base_url = 'http://offensivecommunity.net/'

    # Xpaths
    forum_xpath = '//a[contains(@href, "forumdisplay.php?fid=")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//table/tr[td[contains(@class,"forum")]]'
    thread_first_page_xpath = './/a[contains(@id,"tid_")]/@href'

    thread_last_page_xpath = './/td[contains(@class,"trow")]/div/span'\
                             '/span[@class="smalltext"]/a[last()]/@href'

    thread_date_xpath = './/span[contains(@class,"lastpost")]/span/@title|'\
                        './/span[contains(@class,"lastpost")]/text()[1]'

    thread_pagination_xpath = '//a[@class="pagination_previous"]/@href'

    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//td[@class="tcat"]//span/@title|'\
                      '//td[@class="tcat"]/div/text()'

    avatar_xpath = '//td[contains(@class,"post_avatar")]//img/@src'

    topic_pattern = re.compile(
        r".*tid=(\d+)",
        re.IGNORECASE
    )

    avatar_name_pattern = re.compile(
        r"./avatar_(\d+\.\w+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "On"
    sitemap_datetime_format = '%d-%m-%Y'
    post_datetime_format = '%d-%m-%Y'

    def start_requests(self):
        yield Request(
            url=self.base_url,
            errback=self.check_site_error,
            headers=self.headers
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)

        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
        for forum_url in all_forums:

            full_url = self.base_url + forum_url
            yield Request(
                url=full_url,
                headers=self.headers,
                callback=self.parse_forum
            )

    def parse_thread(self, response):

        # Load all post date
        yield from super().parse_thread(response)

        yield from super().parse_avatars(response)

    def parse_thread_date(self, thread_date):

        if thread_date is None:
            return datetime.today()

        thread_date = thread_date.split(',')[0]
        return dateparser.parse(thread_date)

    def parse_post_date(self, post_date):

        if post_date is None:
            return datetime.today()

        return dateparser.parse(post_date)


class OffensiveCommunityScrapper(SiteMapScrapper):
    spider_class = OffensiveCommunitySpider
    site_name = 'offensivecommunity.net'
    site_type = 'forum'
