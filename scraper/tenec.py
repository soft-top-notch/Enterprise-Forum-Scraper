import re
import uuid

from datetime import (
    datetime,
    timedelta
)
from scrapy import (
    Request,
    FormRequest
)
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)


class TenecSpider(SitemapSpider):
    name = "tenec_spider"

    # Url stuffs
    base_url = "https://tenec.cc/"

    # Xpath stuffs
    forum_xpath = '//div[@id="ipsLayout_mainArea"]//h4[contains(@class, "ipsDataItem_title ipsType_large")]/a/@href'
    pagination_xpath = '//li[@class="ipsPagination_next"]/a/@href'
    
    thread_xpath = '//div[@id="ipsLayout_mainArea"]//div[@class="ipsBox"]/ol/li[contains(@class, "ipsDataItem ipsDataItem_responsivePhoto")]'
    thread_first_page_xpath = './div[@class="ipsDataItem_main"]/h4//a/@href'
    thread_last_page_xpath = './div[@class="ipsDataItem_main"]//ul[contains(@class, "ipsPagination_mini")]/li[@class="ipsPagination_last"]/a/@href'
    thread_date_xpath = './ul[contains(@class, "ipsDataItem_lastPoster")]//time/@datetime'

    thread_pagination_xpath = '//ul[@class="ipsPagination"]/li[@class="ipsPagination_prev"]/a/@href'
    thread_page_xpath = '//ul[@class="ipsPagination"]/li[contains(@class, "ipsPagination_active")]/a/@data-page'
    post_date_xpath = '//div[@class="ipsType_reset"]//time/@datetime'

    avatar_xpath = '//div[@class="cAuthorPane_photo"]//img/@src'

    # Regex stuffs
    avatar_name_pattern = re.compile(
        r".*/(\S+\.\w+)",
        re.IGNORECASE
    )
    pagination_pattern = re.compile(
        r".*page/(\d+)",
        re.IGNORECASE
    )

    use_proxy = "On"

    # Other settings
    sitemap_datetime_format = "%Y-%m-%dT%H:%M:%S"
    post_datetime_format = "%Y-%m-%dT%H:%M:%S"
    
    def start_requests(self):
        # Temporary action to start spider
        yield Request(
            url=self.base_url,
            headers=self.headers,
            callback=self.parse
        )

    def parse_thread_date(self, thread_date):
        """
        :param thread_date: str => thread date as string
        :return: datetime => thread date as datetime converted from string,
                            using class sitemap_datetime_format
        """
        date = None

        try:
            date = datetime.strptime(thread_date.strip().strip('Z'),
                                     self.sitemap_datetime_format)
        except:
            try:
                date = dateparser.parse(thread_date.strip())
            except:
                print(f'Failed to parse ({thread_date}) thread date, so skipping it...')
                pass

        return date

    def parse_post_date(self, post_date):
        """
        :param post_date: str => post date as string
        :return: datetime => post date as datetime converted from string,
                            using class post_datetime_format
        """
        date = None

        try:
            date = datetime.strptime(post_date.strip().strip('Z'),
                                     self.post_datetime_format)
        except:
            try:
                date = dateparser.parse(post_date.strip())
            except:
                print(f'Failed to parse ({post_date}) post date, so skipping it...')
                pass

        return date

    def parse(self, response):

        # Synchronize user agent for cloudfare middleware
        self.synchronize_headers(response)

        # Load all forums
        all_forums = response.xpath(self.forum_xpath).extract()

        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(all_forums))
        
        for forum_url in all_forums:
            # Standardize forum url
            if self.base_url not in forum_url:
                forum_url = response.urljoin(forum_url)

            yield Request(
                url=forum_url,
                headers=self.headers,
                meta=self.synchronize_meta(response),
                callback=self.parse_forum
            )

    def parse_forum(self, response, is_first_page=True):

        # Parse sub forums
        yield from self.parse(response)

        # Parse generic forum
        yield from super().parse_forum(response)

    def parse_thread(self, response):

        # Save generic thread
        yield from super().parse_thread(response)

        # Save avatars
        yield from super().parse_avatars(response)


class TenecScrapper(SiteMapScrapper):
    spider_class = TenecSpider
    site_type = 'forum'


if __name__ == "__main__":
    pass
