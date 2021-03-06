"""Implementation of bing SE"""
import re

import requests

from .registry import SearchEngineFactory
from .search_engine_interface import SearchEngineInterface


@SearchEngineFactory.register_se(name="Bing SE")
class Bing(SearchEngineInterface):  # pylint: disable=too-few-public-methods
    """Implementation of bing image search"""

    BING_IMAGE_URL = "https://www.bing.com/images/async?q="
    USER_AGENT = {
        "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"
    }

    def _collect_img_links(self):
        page = 0
        while len(self._image_urls) < self.n_images:
            search_url = self.BING_IMAGE_URL + self.keyword + "&first=" + str(page) + "&count=100"

            response = requests.get(search_url, headers=self.USER_AGENT)
            html = response.text

            page += 100
            results = re.findall(r"murl&quot;:&quot;(.*?)&quot;", html)
            for link in results:
                self._image_urls.append(link)

                if len(self._image_urls) == self.n_images:
                    break
