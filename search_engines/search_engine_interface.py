from abc import ABC


class SearchEngineInterface(ABC):
    def __init__(self, keyword: str, n_images: int):
        self.image_urls = []
        self.keyword = keyword
        self.n_images = n_images

    def collect_img_links(self):
        raise NotImplementedError
