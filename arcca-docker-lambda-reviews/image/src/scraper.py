import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
import requests
from tempfile import mkdtemp


class GoogleScraper:
    def __init__(self, search_url, is_scraped=0, reviews_from_db=[]):
        self._browser = None
        self._init_browser(search_url)
        self._len_of_reviews_from_db = len(reviews_from_db)
        self._is_scraped = is_scraped
        self._reviews = []
        self._last_index_of_reviews_url = 0
        self._reviews_from_db = reviews_from_db
        self._can_scroll = True
        self._reviews_count_from_web = 0

    def _init_browser(self, search_url):
        options = webdriver.ChromeOptions()
        service = Service("/opt/chromedriver")

        options.binary_location = "/opt/chrome/chrome"
        options.add_argument("--enable-javascript")

        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x1696")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        options.add_argument("--remote-debugging-port=9222")

        self._browser = webdriver.Chrome(options=options, service=service)
        self._browser.request_interceptor = self._interceptor
        self._browser.get(search_url)

    def _interceptor(self, request):
        # Block PNG, JPEG, and GIF images
        if request.path.endswith((".png", ".jpg", ".gif")):
            request.abort()

    def _skip_google_url(self, times):
        for i in range(times):
            # precisei realizar o skip porque ao clicar em ordenar por mais recentes, o google ja fez duas requisicoes
            for index, request in enumerate(self._browser.requests):
                if request.response and "listugcposts" in request.url:
                    self._last_index_of_reviews_url += index
                    break
        self._last_index_of_reviews_url += 1            
            
    def get_reviews_count(self):
        return len(self._reviews)

    def get_updated_reviews(self):
        self._reviews_count_from_web = self.get_reviews_count_from_web()

        if (
            not self._is_scraped
            or self._reviews_count_from_web > self._len_of_reviews_from_db
        ):
            self._click_in_reviews()
            self._click_in_order_reviews()
            self._skip_google_url(1)
            self._get_reviews()
            self._scroll_page()

        self._is_scraped = 1
        return self._reviews

    def _click_in_order_reviews(self):
        try:
            WebDriverWait(self._browser, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, ('//button[@data-value = "Sort"]'))
                )
            )

            time.sleep(2)

            menu_button = self._browser.find_element(
                By.XPATH, '//button[@data-value = "Sort"]'
            )
            menu_button.click()

            WebDriverWait(self._browser, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@role="menu"][@id="action-menu"]')
                )
            )

            menu = self._browser.find_element(
                By.XPATH, '//div[@role="menu"][@id="action-menu"]'
            )
            order_button = menu.find_element(By.XPATH, '//div[@data-index="1"]')
            order_button.click()
        except Exception as e:
            print(e)
            pass

    def _click_in_reviews(self):
        try:
            WebDriverWait(self._browser, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@role = "tablist"]'))
            )
            reviews_tab_list = self._browser.find_element(
                By.XPATH, '//div[@role = "tablist"]'
            )
            reviews_tab = reviews_tab_list.find_elements(
                By.XPATH, '//button[@role = "tab"]'
            )[1]
            reviews_tab.click()
        except Exception as e:
            print(e)
            pass

    def get_reviews_count_from_web(self):
        try:
            xpath = "//span[contains(@aria-label, 'reviews')]"
            WebDriverWait(self._browser, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            time.sleep(3)
            reviews_count_element = self._browser.find_element(By.XPATH, xpath)
            return int(
                reviews_count_element.text.strip().replace("(", "").replace(")", "")
            )
        except Exception as e:
            print(e)
            return 0

    def _scroll_page(self):
        try:
            WebDriverWait(self._browser, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//div[@role = "main"]//div[9]//div//div',
                    )
                )
            )

            role_main = "[role='main']"
            main = f'document.querySelector("{role_main}")'
            scrollable = f"{main}.childNodes[1]"
            scrollable_height = f"{scrollable}.scrollHeight"
            last_height = self._browser.execute_script(f"return {scrollable_height};")
            SCROLL_PAUSE_TIME = 4

            while self._can_scroll:
                self._get_reviews()
                self._browser.execute_script(
                    f"{scrollable}.scrollTo(0, {scrollable_height});"
                )
                time.sleep(SCROLL_PAUSE_TIME)

                new_height = self._browser.execute_script(
                    f"return {scrollable_height};"
                )
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            print(e)
            pass

    def _convert_data_to_review(self, data):
        try:
            for item in data:
                for review_data in item[2]:
                    printable_review = {
                        "reviewer_name": "",
                        "avaliation": "",
                        "comment": "",
                        "date": "",
                    }
                    printable_review["reviewer_name"] = review_data[0][1][4][1][1]
                    try:
                        printable_review["avaliation"] = review_data[0][2][0][0]
                    except:
                        pass
                    try:
                        printable_review["comment"] = review_data[0][2][1][0]
                    except:
                        pass
                    try:
                        printable_review["date"] = review_data[0][1][6]
                    except:
                        pass

                    if self.check_if_review_is_in_db(printable_review):
                        self._can_scroll = False
                        return

                    self._reviews.append(printable_review)
        except Exception as e:
            self._can_scroll = False
            print(e)

    def check_if_review_is_in_db(self, review):
        if self._len_of_reviews_from_db:
            for item in self._reviews_from_db:
                if item[0] == review["reviewer_name"] and item[2] == review["comment"]:
                    return True
        return False
    
    def _get_data_from_url(self, url):
        try:
            custom_header = {"Accept-Encoding": "gzip"}
            response = requests.get(url, headers=custom_header)
            data = json.loads(response.text.replace(")]}'", ""))
            return data
        except:
            return None

    def _get_reviews(self):
        for index, request in enumerate(
            self._browser.requests[self._last_index_of_reviews_url:]
        ):
            if request.response and "listugcposts" in request.url:
                self._last_index_of_reviews_url += index + 1
                url = request.url
                data = self._get_data_from_url(url)
                self._convert_data_to_review([data])
                break

    def quit(self):
        self._browser.quit()
