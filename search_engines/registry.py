class SearchEngineFactory:
    _SEARCH_ENGINES = {}

    @classmethod
    def get_se(cls, name: str, keyword: str, n_images: int, **kwargs):
        if name in cls._SEARCH_ENGINES.keys():
            return cls._SEARCH_ENGINES.get(name)(keyword, n_images, **kwargs)
        else:
            raise ValueError(f"{name} is not a valid SE")

    @classmethod
    def get_names(cls):
        return list(cls._SEARCH_ENGINES.keys())

    @classmethod
    def get_number_of_ses(cls):
        return len(cls._SEARCH_ENGINES)

    @classmethod
    def register_se(cls, name: str):
        def wrapper(_cls):
            cls._SEARCH_ENGINES[name] = _cls
            return _cls
        return wrapper

    @classmethod
    def remove_se(cls, name: str):
        if name in cls._SEARCH_ENGINES.keys():
            cls._SEARCH_ENGINES.pop(name)
            return True
        return False


import search_engines.google
import search_engines.bing
import search_engines.duckgo
