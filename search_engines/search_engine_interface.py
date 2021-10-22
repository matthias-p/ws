"""Interface which any search engine has to implement"""
from abc import ABC
from typing import List


class SearchEngineInterface(ABC):
    """Interface of the search engines. Implement this when you add a new se"""

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
