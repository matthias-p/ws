"""Implementation of google SE"""
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from .search_engine_interface import SearchEngineInterface
from .registry import SearchEngineFactory


@SearchEngineFactory.register_se(name="Google SE")
class Google(SearchEngineInterface):  # pylint: disable=too-few-public-methods
    """
    Implementation of google image search.
    This is the slower compared to bing and duckgo because it has to use selenium.
    This is because by using requests it would only be possible to get the preview image of the
    first 100 images, because javascript needs to be rendered.
    """

    def _collect_img_links(self):
        scrolls = int(self.n_images / 50) + 1
        url = f"https://www.google.com/search?q={self.keyword}&source=lnms&tbm=isch"

        options = Options()
        options.headless = True
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)

        for _ in range(scrolls):
            driver.execute_script("window.scrollBy(0, 1000000)")

        div_number = 1
        while True:
            thumb = driver.find_element(By.XPATH, "/html/body/div[2]/c-wiz/div[4]/div[1]/div/div"
                                                  "/div/div[1]/div[1]/span/div[1]/div[1]/div"
                                                  f"[{div_number}]/a[1]/div[1]/img")

            thumb.click()
            time.sleep(.75)

            element = thumb.find_element(By.XPATH, "//*[@id='Sva75c']/div/div/div[3]/div[2]/c-wiz/"
                                                   "div/div[1]/div[1]/div[2]/div/a/img")

            self._image_urls.append(element.get_attribute("src"))

            div_number += 1
            if len(self._image_urls) == self.n_images:
                break

        driver.quit()
