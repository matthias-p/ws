"""Webscraper config"""

import json
from pathlib import Path


class Config:
    """This class represents a config file for the webscraper"""

    def __init__(self):
        self.dataset_path = None
        self.keywords = None
        self.translations = None
        self.n_samples = None
        self.search_engines = None

    def to_json(self) -> dict:
        """Returns the config as dict"""
        return {
            "dataset_path": self.dataset_path,
            "keywords": self.keywords,
            "translations": self.translations,
            "n_samples": self.n_samples,
            "search_engines": self.search_engines,
        }

    def load_config(self, file_path: Path) -> bool:
        """Loads a config from the given path"""
        if file_path.exists() and file_path.is_file():
            with open(file_path.resolve(), "r", encoding="utf-8") as config_file:
                cfg: dict = json.load(config_file)
            self.dataset_path = cfg.get("dataset_path")
            self.keywords = cfg.get("keywords")
            self.translations = cfg.get("translations")
            self.n_samples = cfg.get("n_samples")
            self.search_engines = cfg.get("search_engines")
            return True
        return False

    def save_config(self, file_path: Path) -> None:
        """Saves config to given path"""
        with open(file_path.resolve(), "w", encoding="utf-8") as config_file:
            json.dump(self.to_json(), config_file)
