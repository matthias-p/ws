"""Implementation of google SE"""
from selenium import webdriver
import selenium.common.exceptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from .search_engine_interface import SearchEngineInterface
from .registry import SearchEngineFactory


@SearchEngineFactory.register_se(name="Google SE")
class Google(SearchEngineInterface):
    def _collect_img_links(self):
        scrolls = int(self.n_images / 50) + 1

        options = Options()
        options.headless = True
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome()

        driver.get("https://google.com/")
        driver.quit()
