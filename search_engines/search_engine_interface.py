"""Interface which any search engine has to implement"""
import hashlib
import io
from abc import ABC
from typing import List

import requests


class SearchEngineInterface(ABC):
    def __init__(self, keyword: str, n_images: int, **kwargs):
        self._image_urls: List[str] = []
        self.keyword = keyword
        self.n_images = n_images
        self.callback = kwargs.get("callback")

        self._collect_img_links()

    def __iter__(self):
        """Iterator over image_urls"""
        yield from self._image_urls

    def _collect_img_links(self):
        """This starts scraping and saves urls to image_urls"""
        raise NotImplementedError

    def get_img_urls(self):
        """Return the image_urls"""
        return self._image_urls

    # def download_urls(self):
    #     for link in self:
    #         try:
    #             r = requests.get(link)
    #         except requests.exceptions.ReadTimeout:
    #             continue
    #         except requests.exceptions.ConnectionError:
    #             continue
    #
    #         bytes_file = io.BytesIO(r.content)
    #
    #         if not self._check_magic_number(bytes_file.read(3)):
    #             continue
    #
    #         img_t = link.rsplit(".", 1)[-1][:3]  # only get 3 chars
    #         md5 = hashlib.md5(bytes_file.getvalue()).hexdigest()
    #         # use hash as name so duplicates are overwritten
    #
    #         with open(f"tests/{md5}.{img_t}", "wb") as img_file:
    #             img_file.write(bytes_file.getvalue())
    #
    # @staticmethod
    # def _check_magic_number(line):
    #     return line in MAGIC_NUMBERS
