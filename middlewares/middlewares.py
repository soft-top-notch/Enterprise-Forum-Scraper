import cloudscraper
import uuid
import re

from scraper.base_scrapper import (
    PROXY_USERNAME,
    PROXY_PASSWORD,
    PROXY
)


class LuminatyProxyMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.logger = crawler.spider.logger
        self.username = PROXY_USERNAME
        self.password = PROXY_PASSWORD
        self.super_proxy_url = PROXY

    def process_request(self, request, spider):

        # Check session
        session = (request.meta.get("cookiejar")
                   or uuid.uuid1().hex)
        country = request.meta.get("country")
        ip = request.meta.get("ip")

        # Init username
        username = self.username

        # Add session string to session if available
        if session and not ip:
            username = "%s-session-%s" % (
                username,
                session
            )

        # Add country to session if available
        if country and not ip:
            username = "%s-country-%s" % (
                username,
                country
            )

        # If has ip meta, make it priority over session
        if ip:
            username = "%s-ip-%s" % (
                username,
                ip
            )

        # Add proxy to request
        request.meta["proxy"] = self.super_proxy_url % (
            username,
            self.password
        )

        # Remove old authorization if exist
        if request.headers.get("Proxy-Authorization"):
            del request.headers["Proxy-Authorization"]


class DedicatedProxyMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.logger = crawler.spider.logger
        self.username = PROXY_USERNAME
        self.password = PROXY_PASSWORD
        self.super_proxy_url = PROXY

    def process_request(self, request, spider):

        # Check session
        session = (request.meta.get("cookiejar")
                   or uuid.uuid1().hex)
        country = request.meta.get("country")
        ip = request.meta.get("ip")

        # Init username
        username = self.username

        # Add session string to session if available
        if session and not ip:
            username = "%s-session-%s" % (
                username,
                session
            )

        # Add country to session if available
        if country and not ip:
            username = "%s-country-%s" % (
                username,
                country
            )

        # If has ip meta, make it priority over session
        if ip:
            username = "%s-ip-%s" % (
                username,
                ip
            )

        # Add proxy to request
        request.meta["proxy"] = self.super_proxy_url % (
            username,
            self.password
        )

        # Remove old authorization if exist
        if request.headers.get("Proxy-Authorization"):
            del request.headers["Proxy-Authorization"]


class BypassCloudfareMiddleware(object):

    captcha_provider = "2captcha"
    captcha_token = "76228b91f256210cf20e6d8428818e23"

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    @staticmethod
    def is_cloudflare_challenge(response):
        """Test if the given response contains the cloudflare's anti-bot protection"""

        first_cloudfare_text = "jschl_vc"
        second_cloudfare_text = "jschl_answer"
        third_cloudfare_text = "Cloudflare Ray ID"
        fourth_cloudfare_text = "cf.challenge.js"
        first_recaptcha_text = "Why do I have to complete a CAPTCHA"
        second_recaptcha_text = "cf_chl_captcha_tk"

        cloudfare_test = ((response.status in (503, 429, 403)
                           and response.headers.get("Server", "").startswith(b"cloudflare")
                           and first_cloudfare_text in response.text
                           and second_cloudfare_text in response.text)
                          or (response.status in (503, 429, 403)
                              and first_recaptcha_text in response.text
                              and third_cloudfare_text in response.text)
                          or (response.status in (503, 429, 403)
                              and second_recaptcha_text in response.text))

        return cloudfare_test

    def __init__(self, crawler):
        # Load logger
        self.logger = crawler.spider.logger

        # Load spider settings
        self.allow_retry = getattr(crawler.spider, "cloudfare_allow_retry", 5)
        self.delay = getattr(crawler.spider, "cloudfare_delay", 5)
        self.solve_depth = getattr(crawler.spider, "cloudfare_solve_depth", 5)
        self.fraudulent_threshold = getattr(crawler.spider, "fraudulent_threshold", 35)
        self.ip_batch_size = getattr(crawler.spider, "ip_batch_size", 20)

        # Load ip handler
        from middlewares.utils import IpHandler
        self.ip_handler = IpHandler(
            logger=self.logger,
            fraudulent_threshold=self.fraudulent_threshold,
            ip_batch_size=self.ip_batch_size
        )

    def load_cookies(self, request, byte=True):
        cookies = {}

        # Load cookies bytes
        cookies_string = request.headers.get("Cookie")
        if byte:
            cookies_string = request.headers.get("Cookie").decode("utf-8")

        # Convert cookie byte
        if cookies_string is not None:
            cookies_elements = [
                element.strip().split("=") for element in cookies_string.split(";")
            ]
            cookies = {
                element[0]: "=".join(element[1:]) for element in cookies_elements
            }

        return cookies

    def get_ip_from_proxy(self, proxy):
        # Init regex method
        check_ip = re.compile(
            r"(?<=ip\-).*?(?=\-|\:)",
            re.IGNORECASE
        )

        # Return ip
        try:
            return check_ip.search(proxy).group()
        except Exception as err:
            return

    def get_cftoken(self, url, proxy=None):
        session = cloudscraper.create_scraper(
            delay=self.delay,
            recaptcha={
                "provider": self.captcha_provider,
                "api_key": self.captcha_token
            }
        )
        ip = None

        request_args = {
            "url": url,
        }

        if proxy:
            request_args["proxies"] = {
                "http": proxy,
                "https": proxy
            }
            ip = self.get_ip_from_proxy(proxy)
            self.logger.info(
                "Trying this ip: %s" % ip
            )

        response = session.get(**request_args)
        response = session.get(**request_args)

        headers = response.request.headers
        cookies = self.load_cookies(response.request, False)

        return cookies, headers, ip

    def process_response(self, request, response, spider):

        if not self.is_cloudflare_challenge(response):
            return response

        # Init request args
        request_args = {}

        # Add proxy if available
        proxy = request.meta.get("proxy")
        if proxy:
            request_args["proxy"] = proxy

        # Add proxy authen if available
        basic_auth = request.headers.get("Proxy-Authorization")
        if basic_auth:

            # Load good ip
            ip = self.ip_handler.get_good_ip()

            # Rebuild proxy with good ip
            root_proxy = proxy.replace(
                "https://", ""
            ).replace(
                "http://", ""
            )
            username = "%s-ip-%s" % (
                PROXY_USERNAME,
                ip
            )
            password = PROXY_PASSWORD
            request_args["proxy"] = "%s:%s@%s" % (
                username,
                password,
                root_proxy
            )

        retry = 0
        while True:
            try:
                cookies, headers, ip = self.get_cftoken(
                    request.url,
                    **request_args
                )
                break
            except Exception as err:
                self.logger.info(err)
                if not basic_auth:
                    raise RuntimeError(
                        "Protection loop, already try 3 time."
                    )
                elif retry < self.allow_retry:
                    proxy = PROXY % (
                        "%s-ip-%s" % (
                            PROXY_USERNAME,
                            self.ip_handler.get_good_ip()
                        ),
                        PROXY_PASSWORD
                    )
                    request_args["proxy"] = proxy
                    retry += 1
                    continue

                return response

        # Replace cookies
        request.cookies.update(cookies.copy())

        # Replace user agent
        request.headers.update(headers.copy())

        # Dont filter this retry request
        request.dont_filter = True

        # Add ip meta if exist
        if ip:
            request.meta["ip"] = ip

        self.logger.info(
            "Header after cloudfare check: %s" % request.headers
        )

        self.logger.info(
            "Cookies after cloudfare check: %s" % request.cookies
        )

        return request
