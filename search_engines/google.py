"""Implementation of google SE"""

from .search_engine_interface import SearchEngineInterface
from .registry import SearchEngineFactory


@SearchEngineFactory.register_se(name="Google SE")
class Google(SearchEngineInterface):
    def _collect_img_links(self):
        pass
