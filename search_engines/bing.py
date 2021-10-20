"""Implementation of bing SE"""

from .search_engine_interface import SearchEngineInterface
from .registry import SearchEngineFactory


@SearchEngineFactory.register_se(name="Bing SE")
class Bing(SearchEngineInterface):

    def __init__(self, keyword: str, n_images: int):
        super().__init__(keyword=keyword, n_images=n_images)

    def collect_img_links(self):
        pass
