"""This contains the factory for the search engines"""


class SearchEngineFactory:
    """Implementation of the Factory Pattern"""
    _SEARCH_ENGINES = {}

    @classmethod
    def get_se(cls, name: str, keyword: str, n_images: int, **kwargs):
        """This returns an initialized object of the search engine given by the name"""
        if name in cls._SEARCH_ENGINES:
            return cls._SEARCH_ENGINES.get(name)(keyword, n_images, **kwargs)
        raise ValueError(f"{name} is not a valid SE")

    @classmethod
    def get_names(cls):
        """Returns a list of the names of registered search engines"""
        return list(cls._SEARCH_ENGINES.keys())

    @classmethod
    def get_number_of_ses(cls):
        """Returns how many search engines are currently registered"""
        return len(cls._SEARCH_ENGINES)

    @classmethod
    def register_se(cls, name: str):
        """This can be used to decorate a class and register it in the factory"""
        def wrapper(_cls):
            cls._SEARCH_ENGINES[name] = _cls
            return _cls
        return wrapper

    @classmethod
    def remove_se(cls, name: str):
        """This can be used to remove a search engine from the factory"""
        if name in cls._SEARCH_ENGINES:
            cls._SEARCH_ENGINES.pop(name)
            return True
        return False


# Disable all the import warnings at this point. This is intended
# pylint: disable=unused-import,wrong-import-position,cyclic-import
import search_engines.google
import search_engines.bing
import search_engines.duckgo
