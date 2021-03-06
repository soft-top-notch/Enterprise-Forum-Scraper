import json
import re
import os
from os import listdir
from os.path import isfile, join

import datetime
import time
import scrapy
import traceback
from scraper.base_scrapper import (
    SitemapSpider,
    SiteMapScrapper
)
from scraper.base_scrapper import PROXY_USERNAME, PROXY_PASSWORD, PROXY

MIN_DELAY=0.3
MAX_DELAY=0.6
API_KEY = '90f95ac404308e553c1fa65bdec5388c'
NO_OF_THREADS = 13

class PsbdmpSpider(SitemapSpider):
    name = 'psbdmp_spider'
    base_url = 'https://psbdmp.ws'
    start_url = 'https://psbdmp.ws/api/v3/getbydate'
    dump_url = f'https://psbdmp.ws/api/v3/dump/{{}}?key={API_KEY}'

    # Other settings
    use_proxy = "On"
    download_thread = NO_OF_THREADS
    
    time_format = "%Y-%m-%d %H:%M:%S"
    date_format = "%Y-%m-%d"

    def start_requests(self,):
        self.limit_time = self.start_date

        if not self.start_date:
            self.start_date = datetime.datetime.now()
        if not self.end_date:
            self.end_date = datetime.datetime.now()
        self.start_date = self.start_date - datetime.timedelta(days=1)
        while self.start_date <= self.end_date:
            _from = self.start_date.strftime(self.date_format)
            self.start_date = self.start_date + datetime.timedelta(days=1)
            _to = _from
            formdata = {
                'from': _from,
                'to': _to
            }
            output_path = '{}/{}'.format(self.output_path, _from)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            yield scrapy.FormRequest(
                self.start_url,
                formdata=formdata,
                dont_filter=True,
                method='POST',
                meta={
                    'output_path': output_path,
                    'date': _from
                }
            )

    def parse(self, response):
        json_data = json.loads(response.text)
        data = json_data[0]
        output_path = response.meta['output_path']
        date = response.meta['date']

        onlyfiles = [f.split(".")[0] for f in listdir(output_path) if isfile(join(output_path, f))]
        data = [item for item in json_data[0] if item['id'] not in onlyfiles]
        if self.limit_time:
            data = [item for item in data if int(item['date']) > self.limit_time.timestamp()]

        print(f'Paste count for {date}: {len(data)}')

        for item in data:
            dump_id = item['id']
            dump_url = self.dump_url.format(dump_id)
            yield scrapy.Request(
                dump_url,
                callback=self.save_file,
                meta={
                    'dump_id': dump_id,
                    'output_path': response.meta['output_path']
                }
            )

    def save_file(self, response):
        output_path = response.meta['output_path']
        dump_id = response.meta['dump_id']
        dump_file = '{}/{}.txt'.format(
            output_path, dump_id
        )
        if os.path.exists(dump_file):
            print('{} already exists..!'.format(dump_file))
            return

        try:
            json_data = json.loads(response.text)
        except:
            return

        content = json_data["content"]
        if not content:
            return

        with open(dump_file, 'w') as f:
            f.write(content)
        print('{} done..!'.format(dump_file))
        self.crawler.stats.inc_value("mainlist/detail_saved_count")

class PsbdmpScrapper(SiteMapScrapper):
    spider_class = PsbdmpSpider
    site_name = 'psbdmp.ws'
    site_type = 'paste'

    def load_settings(self):
        settings = super().load_settings()
        settings.update(
            {
                "AUTOTHROTTLE_ENABLED": True,
                "AUTOTHROTTLE_START_DELAY": MIN_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": MAX_DELAY
            }
        )
        return settings
