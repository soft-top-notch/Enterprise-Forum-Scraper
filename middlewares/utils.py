import uuid
import asyncio
import aiohttp
import json

from scrapy import Selector


class IpHandler(object):

    ip_api = "https://api.ipify.org/?format=json"
    fraudulent_api = "https://scamalytics.com/ip/%s"

    def __init__(self, **kwargs):
        from scraper.base_scrapper import (
            VIP_PROXY_USERNAME,
            VIP_PROXY_PASSWORD,
            VIP_PROXY,
            PROXY_USERNAME,
            PROXY_PASSWORD,
            PROXY
        )
        self.use_vip_proxy = kwargs.get("use_vip_proxy")
        self.logger = kwargs.get("logger")
        self.fraudulent_threshold = kwargs.get("fraudulent_threshold", 50)
        self.ip_batch_size = kwargs.get("ip_batch_size", 20)
        if self.use_vip_proxy:
            self.proxy_username = VIP_PROXY_USERNAME
            self.proxy_password = VIP_PROXY_PASSWORD
            self.proxy = VIP_PROXY
        else:
            self.proxy_username = PROXY_USERNAME
            self.proxy_password = PROXY_PASSWORD
            self.proxy = PROXY

    async def fetch(self, url, **kwargs):

        # Load session
        session = aiohttp.ClientSession()

        # Load method
        method = kwargs.get("method")
        if method not in ["get", "post"]:
            method = "get"
        else:
            del kwargs["method"]

        # Load response
        if method == "get":
            response = await session.get(url, **kwargs)
        else:
            response = await session.post(url, **kwargs)

        # Load text response
        try:
            text = await response.text()
        except Exception as err:
            text = None

        # Close session
        await session.close()

        return text

    async def get_fraud_score(self, ip):
        
        try:
            # Load response
            response = await self.fetch(self.fraudulent_api % ip)

            # Load selector
            selector = Selector(text=response)

            # Load score
            score = selector.xpath(
                "//div[@class=\"score\"]/text()"
            ).extract_first()
        except Exception as err:
            score = None

        if not score:
            return self.fraudulent_threshold

        # Standardize score
        score = int(score.split()[-1])

        return score

    async def get_ip_score(self, session_id):

        # Load proxy
        while True:
            try:
                username = "%s-session-%s" % (
                    self.proxy_username,
                    session_id
                )
                response = await self.fetch(
                    self.ip_api,
                    proxy=self.proxy % (
                        username,
                        self.proxy_password
                    )
                )
                break
            except Exception as err:
                session_id = uuid.uuid1().hex
                continue

        # Load ip
        ip = json.loads(response).get("ip")

        # Load score
        score = await self.get_fraud_score(ip)

        return ip, score

    def loop_good_ip(self):
        request_pool = []
        index = 0
        while index < self.ip_batch_size:
            index += 1
            session_id = uuid.uuid1().hex
            request_pool.append(
                self.get_ip_score(session_id)
            )

        # Load loop
        loop = asyncio.get_event_loop()

        # Load loop results
        results = loop.run_until_complete(
            asyncio.gather(*request_pool)
        )

        # Sort result
        results.sort(key=lambda x: x[1])

        return results[0]

    def get_good_ip(self):

        while True:
            ip, score = self.loop_good_ip()
            if score >= self.fraudulent_threshold:
                self.logger.info(
                    "Ip %s has fraudulent score of %s, "
                    "above threshold %s, aborting." % (
                        ip, score, self.fraudulent_threshold
                    )
                )
                continue

            # Report good ip
            self.logger.info(
                "Find out good ip %s with fraudulent score of %s, "
                "below threshold %s, continue." % (
                    ip, score, self.fraudulent_threshold
                )
            )

            return ip
