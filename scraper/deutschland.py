import re
from scrapy.http import Request
from scraper.base_scrapper import SitemapSpider, SiteMapScrapper


PROXY = 'http://127.0.0.1:8118'


class DeutschLandSpider(SitemapSpider):
    name = 'deutschland_spider'
    base_url = 'http://germany2igel45jbmjdipfbzdswjcpjqzqozxt4l33452kzrrda2rbid.onion/'

    # Xpaths
    forum_xpath = '//a[contains(@href, "forum-")]/@href'
    pagination_xpath = '//div[@class="pagination"]'\
                       '/a[@class="pagination_next"]/@href'
    thread_xpath = '//tr[@class="inline_row"]'
    thread_first_page_xpath = './/span[contains(@id,"tid_")]/a/@href'
    thread_last_page_xpath = './/td[contains(@class,"forumdisplay_")]/div'\
                             '/span/span[@class="smalltext"]/a[last()]/@href'
    thread_date_xpath = './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/text()[1]|'\
                        './/td[contains(@class,"forumdisplay")]'\
                        '/span[@class="lastpost smalltext"]/span/@title'
    thread_pagination_xpath = '//div[@class="pagination"]'\
                              '//a[@class="pagination_previous"]/@href'
    thread_page_xpath = '//span[@class="pagination_current"]/text()'
    post_date_xpath = '//span[@class="post_date"]/text()[1]|'\
                      '//span[@class="post_date"]/span/@title'\

    topic_pattern = re.compile(
        r".*thread-(\d+)",
        re.IGNORECASE
    )

    # Other settings
    use_proxy = "Tor"
    sitemap_datetime_format = '%d-%m-%Y, %H:%M'
    post_datetime_format = '%d-%m-%Y, %H:%M'

    def synchronize_meta(self, response, default_meta={}):
        meta = {
            key: response.meta.get(key) for key in ["cookiejar", "ip"]
            if response.meta.get(key)
        }

        meta.update(default_meta)
        meta.update({'proxy': PROXY})

        return meta
        
    def start_requests(self):
        yield Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                'proxy': PROXY
            },
            dont_filter=True,
            errback=self.check_site_error
        )

    def parse(self, response):
        # Synchronize cloudfare user agent
        self.synchronize_headers(response)
        all_forums = set(response.xpath(self.forum_xpath).extract())
        self.forums.update(all_forums)
        # update stats
        self.crawler.stats.set_value("mainlist/mainlist_count", len(self.forums))

        for forum_url in all_forums:
            yield response.follow(
                url=forum_url,
                headers=self.headers,
                callback=self.parse_forum,
                meta=self.synchronize_meta(response),
            )

    def parse_thread(self, response):

        # Parse generic thread
        yield from super().parse_thread(response)


class DeutschLandScrapper(SiteMapScrapper):

    spider_class = DeutschLandSpider
    site_name = 'deutschland_germanyruvvy2tcw'
    site_type = 'forum'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "RETRY_HTTP_CODES": [406, 429, 500, 503],
            }
        )
        return settings
