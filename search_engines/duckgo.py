"""Implementation of duckgo SE"""
import json
import re

import requests

from .search_engine_interface import SearchEngineInterface
from .registry import SearchEngineFactory


@SearchEngineFactory.register_se(name="Duckgo SE")
class DuckGo(SearchEngineInterface):
    def _collect_img_links(self):
        url = "https://duckduckgo.com/"
        params = {"q": self.keyword}
        headers = {
            "authority": "duckduckgo.com",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "sec-fetch-dest": "empty",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "referer": "https://duckduckgo.com/",
            "accept-language": "en-US,en;q=0.9"
        }

        res = requests.post(url, data=params, timeout=3.000)
        search_object = re.search(r'vqd=([\d-]+)&', res.text, re.M | re.I)

        params = (
            ("l", "us-en"),
            ("o", "json"),
            ("q", self.keyword),
            ("vqd", search_object.group(1)),
            ("f", ",,,"),
            ("p", "1"),
            ("v7exp", "a")
        )

        request_url = url + "i.js"

        while len(self._image_urls) < self.n_images:
            res = requests.get(request_url, headers=headers, params=params)
            data = json.loads(res.text)

            for result in data.get("results"):
                self._image_urls.append(result.get("image"))

                if len(self._image_urls) == self.n_images:
                    break

            if "next" not in data:
                return
            request_url = url + data.get("next")
