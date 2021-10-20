"""Implementation of duckgo SE"""

from .search_engine_interface import SearchEngineInterface
from .registry import SearchEngineFactory


@SearchEngineFactory.register_se(name="Duckgo SE")
class DuckGo(SearchEngineInterface):

    def __init__(self, keyword: str, n_images: int):
        super().__init__(keyword=keyword, n_images=n_images)

    def collect_img_links(self):
        pass
