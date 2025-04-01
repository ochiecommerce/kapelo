import string, os, time, random, traceback, json, re

from random import randint

from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    UnexpectedAlertPresentException,
)
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from session_utils import SerializableMixin
from utils import search_file


class SimpleWorker:
    """
    Represents an online worker
    """

    def __init__(
        self,
        driver: WebDriver = None,
        max_wait: int = 5,
        name="worker",
        home_page=None,
    ) -> None:
        self.locators = {}
        self.max_wait = max_wait
        self._driver: WebDriver = driver
        self.name = name
        self.wait_time = 30
        self.running = False

        if home_page:
            driver.get(home_page)
        
        self.home_page = home_page

        self.main_window = driver.current_window_handle

    def set_locators(self, **locators):
        """
        Set element locators for this worker
        """
        for key, value in locators.items():
            self.locators[key] = value

    @property
    def wait(self) -> WebDriverWait[WebDriver]:
        return WebDriverWait(self._driver, self.wait_time)

    def check(self, element_id) -> bool:
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, element_id)))
            return True
        except TimeoutException:
            return False

    def check_recapture(self):
        return self.check("rc-anchor-container")

    def check_signup(self):
        return self.check("signup_password")

    def check_login(self):
        return self.check("login_password")

    @property
    def driver(self):
        """The webdriver instance being used"""
        return self._driver

    def close_driver(self):
        try:
            self._driver.close()

        except UnexpectedAlertPresentException:
            Alert(self._driver).accept()
            self._driver.close()

    def random_click(self, element: WebElement):
        """Click a web element after a random wait time"""
        self.scroll_to(element)
        actions = ActionChains(self.driver)
        try:
            #self.driver.execute_script("arguments[0].click();", element)
            actions.move_to_element(element).click().perform()

        except StaleElementReferenceException:
            self.repair()

    def scroll_to(self, element:WebElement):
        """Scroll to a web element"""
        self.driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", element)
        time.sleep(randint(1, self.max_wait))

    def initialize(self):
        """Implement your worker initialization code here"""
        self.driver.get(self.home_page)

    def set_driver(self, driver):
        """replace driver and reinitialize"""
        self._driver = driver
        self.initialize()

    def repair(self):
        """Repair errors that may arise in work session"""
        # Try to accept any alert on the window
        try:
            Alert(self._driver).accept()
        except Exception:
            pass

        # Refresh window
        self._driver.refresh()

        # Resume work
        self.work()

    def work(self):
        """Start work session, override this method in your worker implementation"""
        self.running = True

    @property
    def status(self):
        """Status of the work page"""
        if "Earn" in self.driver.title:
            return "Searching"
        elif "Time Elapsed" in self.driver.title:
            return "Working"



class Worker(SimpleWorker, SerializableMixin):
    def __init__(self, driver=None, max_wait=5, name="worker", home_page=None):
        super().__init__(driver, max_wait, name, home_page)
        self.refuge_window = None

    def open_new_tab(self) -> str:
        """Open a new tab"""
        initial_handles_count = len(self.driver.window_handles)
        # Open a new tab
        self.driver.execute_script("window.open('about:blank')")
        WebDriverWait(self.driver, 60).until(
            lambda driver: len(driver.window_handles) > initial_handles_count
        )

        self.refuge_window: str = self.driver.window_handles[-1]
        return self.refuge_window

    def close_tab(self, tab_handle):
        """Close a tab"""
        self._driver.switch_to.window(tab_handle)
        self._driver.close()
        self._driver.switch_to.window(self.main_window)


class CounterMixin:
    @property
    def wallet(self):
        counter2 = self.driver.find_element(By.ID, "counter2")
        return counter2.text

    @property
    def bonus(self):
        counter44 = self.driver.find_element(By.ID, "counter44")
        return counter44.text

    @property
    def earnings(self):
        counter = self.driver.find_element(By.ID, "counter")
        return counter.text

    @property
    def referral(self):
        counter3 = self.driver.find_element(By.ID, "counter3")
        return counter3.text


class Ad(SimpleWorker):
    def __init__(self, driver):
        super().__init__(driver)
        self.timer = self.id = None
        self.locators["view"] = (
            By.CSS_SELECTOR,
            "#viewAdsTOffers1 > tbody > tr > td:nth-child(4) > div > a.btnClickAdd > span > input",
        )
        self.locators["no_ads"] = (
            By.CSS_SELECTOR,
            "#viewAdsTOffers1 > tbody > tr:nth-child(2) > td > strong",
        )
        self.view: WebElement = self.wait.until(
            EC.any_of(
                EC.presence_of_element_located(self.locators["view"]),
                EC.presence_of_element_located(self.locators["no_ads"]),
            )
        )

        if self.view.tag_name == "input":
            self.timer = int(
                driver.execute_script(
                    "return document.getElementsByClassName('btnClickAdd')[0].getAttribute('data-timer')"
                )
            )

            self.id = driver.execute_script(
                "return document.getElementsByClassName('btnClickAdd')[0].getAttribute('data-ad-id')"
            )


class ContentWorker(Worker, CounterMixin):
    """Worker implementation for watching ads in timebucks"""

    def __init__(self, driver=None, max_wait=5, name="worker"):
        super().__init__(
            driver,
            max_wait,
            name,
            home_page="https://timebucks.com/publishers/index.php?pg=earn&tab=view_content_ads",
        )
        self.is_earn_page: bool = self._driver.title == "Earn"
        if not self.is_earn_page:
            print("page title", self._driver.title)
        self.no_ads = None
        self.ad_ids = []
        ad = Ad(self.driver)
        if ad.view.tag_name == "input":

            self.open_new_tab()

        else:
            self.no_ads = True

    def work(self) -> int:
        super().work()
        results = 0
        if self.no_ads:
            return 0

        if self.is_earn_page:
            results: int = self.handle_content()

        self.close_tab(self.refuge_window)
        return results

    def handle_content(self) -> int:
        """Watch ads"""
        while self.running:
            try:
                ad = None
                try:
                    ad = Ad(self._driver)
                    if ad.id in self.ad_ids:
                        self.repair()
                        break

                except UnexpectedAlertPresentException:
                    Alert(self._driver).accept()
                    self.repair()

                if ad.timer:
                    if ad.timer > 0:
                        self.random_click(ad.view)
                        try:
                            Alert(self._driver).accept()
                            continue
                        except Exception:
                            pass

                        try:
                            self.wait.until(EC.number_of_windows_to_be(3))

                        except TimeoutException:
                            self.repair()
                            break
                        ad_window = self._driver.window_handles[2]
                        self.close_tab(ad_window)
                        self._driver.switch_to.window(self.refuge_window)
                        time.sleep(ad.timer + 1)
                        self._driver.switch_to.window(self.main_window)
                        self.ad_ids.append(ad.id)

                    else:
                        break

                else:
                    break
            except Exception:
                traceback.print_exc()
                break

        return len(self.ad_ids)


def random_string(len=10) -> str:
    return "".join(random.choices(string.ascii_letters, k=len))


class VideoThumbnail(Worker):
    """
    VideoThumbnail is a worker class that handles the process of checking the availability of a video on a webpage based on its thumbnail.
    Attributes:
        driver (WebDriver): The WebDriver instance used to interact with the browser.
        thumbnail_tab (str): The handle of the newly opened tab where the thumbnail is checked.
    Methods:
        __init__(driver: WebDriver, url: str):
            Initializes the VideoThumbnail instance, opens a new tab, and navigates to the provided URL.
        available() -> bool:
            Checks if a video is available on the page based on the thumbnail URL.
            Returns True if the video is available, False otherwise.
    """

    def __init__(self, driver: WebDriver, url: str):
        super().__init__(driver)
        self.thumbnail_tab = self.open_new_tab()
        self.driver.switch_to.window(self.thumbnail_tab)
        self.driver.get(url)

    @property
    def available(self) -> bool:
        """
        Check if a video is available on a page based on the thumbnail URL.
        Args:
            driver (WebDriver): The WebDriver instance to use.
            thumbnail_url (str): The URL of the video thumbnail image.
            Returns:
                bool: True if the video is available, False otherwise.
        """
        available=False
        try:
            img: WebElement = self.driver.find_element(By.TAG_NAME, "img")
            available: bool = int(img.get_attribute("naturalWidth")) > 200
            
        except:
            pass

        finally:
            self.close_tab(self.thumbnail_tab)
            return available
        
from models import ProblematicVideo
class YouTube(Worker):
    def __init__(self, driver, playback=2, name="YouTube bot"):
        super().__init__(driver=driver, name=name)
        self.playback = playback
        self.screenshot = "image.png"
        self.current_vid = None
        self.driver.set_script_timeout(30)
        self.driver.set_page_load_timeout(30)
        self.set_locators(skip_ad=(By.CLASS_NAME, "ytp-skip-ad-button"))
        self.screenshots_folder = 'screenshots'

    def skip_ad(self):
        """
        Waits for the 'skip ad' button to become visible and clicks it.

        This method uses an explicit wait to ensure that the 'skip ad' button
        is visible before attempting to click it. The locator for the 'skip ad'
        button is expected to be stored in the `self.locators` dictionary with
        the key 'skip_ad'.

        Raises:
            TimeoutException: If the 'skip ad' button does not become visible
                              within the allotted time.
        """
        skip_ad: WebElement = WebDriverWait(self._driver, 15).until(
            EC.visibility_of_element_located(self.locators["skip_ad"])
        )
        skip_ad.click()

    def set_playback(self, playback):
        """
        Sets the playback rate of the first video element on the page.

        Args:
            playback (float): The desired playback rate for the video.
        """
        self._driver.execute_script(
            f"document.getElementsByTagName('video')[0].playbackRate = {playback}"
        )

    def search_and_click(self, vid):
        """Searches for a YouTube video link on the current page and clicks it. If the link is not found, scrolls down the page until the link is found and clicked. If an error occurs, navigates directly to the video URL.

        Args:
            vid (str): The video ID of the YouTube video to search for.

        Raises:
            Exception: If an error occurs during the execution of the JavaScript code.
        """

        js = f"""
var callback = arguments[arguments.length - 1];
let target = document.querySelector('a[href*="{vid}"]');
function step() {{
    if(target){{
        target.click()
        callback()
        }}
    else{{
        window.scrollTo({{top: document.body.scrollHeight, behavior: 'smooth'}})
        target=document.querySelector('a[href*="{vid}"]')
        setTimeout(step, 1000)
        }}
}}
step()
"""
        try:
            self.driver.execute_async_script(js)

        except TimeoutException:
            self.watch_id(vid)

    def watch_id(self, video_id):
        """
        Watch a YouTube video of a given id
        """
        return self.watch(f"https://www.youtube.com/watch?v={video_id}")

    def watch(
        self,
        absolute_link,
    ):
        """
        Opens a video in youtube with;
        absolute_link: as the link of the video,
        watch it for the given duration (default duration = 60 seconds)
        screenshot: if true screenshot the page after watching (default True)
        """

        self.driver.switch_to.new_window("tab")
        self.driver.get(absolute_link)

    def control(
        self,
        duration=60,
        n_screenshots=1
    ):
        """
        1.  wait for a video to play for the given duration
        2.  pause the video
        3.  take screenshot of the page and save as self.screenshot
        """
        try:
            self.skip_ad()
        except Exception:
            pass
        try:
            current_time = 0
            self.set_playback(self.playback)
            video = self.driver.find_element(By.CSS_SELECTOR,'video')
            video_duration = video.get_property('duration')
            
            if video_duration<duration:
                duration = video_duration-2
                
            while current_time < duration:
                time.sleep(9)
                current_time = video.get_property('currentTime')
                if current_time==0:
                    new_problematic = ProblematicVideo(vid=self.current_vid)
                    new_problematic.save()
                    return False

            video_player: WebElement = self._driver.find_element(
                By.CSS_SELECTOR, "div.html5-video-player"
            )
            

            if self.screenshot:
                for i in range(n_screenshots):
                    # Pause the video (simulate pressing the spacebar)
                    video_player.send_keys(" ")
                    time.sleep(1)
                    self._driver.save_screenshot(self.screenshots_folder+os.sep+self.screenshot+f"_{random_string()}.png")
                    video_player.send_keys(" ")
                    time.sleep(1)
                    x= video.get_property('currentTime')
                    y=video.get_property('duration')
                    remaining = y-x
                    if remaining <2:
                        break
            return search_file(self.screenshots_folder,self.screenshot)
        except Exception:
            traceback.print_exc()
            return False

    def do_task(self, instructions):
        """
        Executes a task based on the provided instructions.

        Args:
            tr1 (dict): A dictionary containing task instructions.

        Returns:
            Any: The result of the control method.

        The method performs the following steps:
        1. Extracts URLs from the task instructions using YouTube.get_urls.
        2. Prints the extracted URLs.
        3. Retrieves the video ID from the second URL.
        4. Navigates the driver to the first URL.
        5. Searches for and clicks on the video using the video ID.
        6. Waits for 5 seconds.
        7. Calls and returns the result of the control method.
        """
        urls: list[str] = YouTube.get_urls(instructions)
        print("urls", urls)
        
        vid: str = YouTube.video_id(urls[-1])
        
        self.screenshot = vid

        if len(urls) == 2:
            # check if the first url is a youtube video
            thumbnail = VideoThumbnail(self.driver, urls[1])
            if not thumbnail.available:
                print("Thumbnail not available")
                return False

            
            problematic = ProblematicVideo.select().where(ProblematicVideo.vid == vid)
            if problematic:
                print(f"Video {vid} is problematic")
                return False
            
            
            self.current_vid = vid
            self.driver.get(urls[0])

            if not vid:
                return False
            self.search_and_click(
                vid,
            )
        elif len(urls) == 1:
            self.driver.get(urls[0])

        return self.control(n_screenshots=5)

    @staticmethod
    def get_urls(text):
        """
        Extracts all URLs from the given text.
        Args:
            text (str): The input text from which URLs need to be extracted.
        Returns:
            list: A list of URLs found in the input text.
        """
        # Regular expression pattern to match URLs
        url_pattern = r"https?://[^\s]+"

        # Find all URLs in the text
        urls = re.findall(url_pattern, text)

        return urls

    @staticmethod
    def video_id(url):
        """
        Extracts the video ID from a given YouTube thumbnail URL.
        Args:
            url (str): The URL of the YouTube thumbnail image.
        Returns:
            str: The extracted video ID if found, otherwise None.
        Example:
            >>> video_id('https://i.ytimg.com/vi/abc123/default.jpg')
            'abc123'
        """
        # Regular expression to extract the video ID
        pattern = r"\.com/vi/([^/]+)/[a-z]+"

        # Search for the pattern in the URL
        match = re.search(pattern, url)

        # Extract and print the video ID
        video_id = None
        if match:
            video_id = match.group(1)
            print(f"Video ID: {video_id}")
        else:
            print(f"No video ID found in {url}")

        return video_id


class TrArray:
    """
    A class used to represent an array of task dictionaries and provide filtering capabilities.
    Attributes
    ----------
    trArray : list[dict[str, str]]
        A list of dictionaries where each dictionary represents a task with string keys and values.
    Methods
    -------
    filter(column, value)
        Filters the tasks based on the specified column and value, returning a new TrArray instance with the filtered tasks.
    regex_filter(column, value)
        Filters the tasks based on the specified column and a substring value, returning a new TrArray instance with the filtered tasks.
    """

    def __init__(self, trArray) -> None:
        self.trArray: list[dict[str, str]] = trArray

    def filter(self, column, value) -> "TrArray":
        """
        Filters the trArray based on the specified column and value.
        Args:
            column (str): The column name to filter by.
            value (Any): The value to filter for in the specified column.
        Returns:
            TrArray: A new TrArray instance containing the filtered results.
        """
        new = []
        for tr in self.trArray:
            if tr[column] == value:
                new.append(tr)

        return TrArray(new)

    def regex_filter(self, column, value) -> "TrArray":
        """
        Filters the rows in trArray based on whether the specified column contains the given value.
        Args:
            column (int): The index of the column to search within each row.
            value (str): The substring to search for within the specified column.
        Returns:
            TrArray: A new TrArray object containing rows where the specified column contains the given value.
        """
        new = []
        for tr in self.trArray:
            if tr[column].find(value) > 0:
                new.append(tr)

        return TrArray(new)
    
    def sort_by(self,column):
        return TrArray(sorted(self.trArray,key=lambda x:x[column],reverse=True))


class YtTasksSurveyer(Worker):
    """YtTasksSurveyer is a class that inherits from the Worker class and is responsible for surveying YouTube tasks on the TimeBucks platform.
    Attributes:
        driver (WebDriver): The Selenium WebDriver instance used to interact with the web page.
        home_page (str): The URL of the "Earn" page on the TimeBucks platform.
    Methods:
        __init__(self, driver=None):
            Initializes the YtTasksSurveyer instance with the provided WebDriver and sets the home page URL.
        get_tr_data(self):
        survey(self) -> list[dict[str, str]]:"""

    def __init__(self, driver=None):
        super().__init__(
            driver,
            home_page="https://timebucks.com/publishers/index.php?pg=earn&tab=tasks_tasks",
        )

    def get_tr_data(self):
        """
        Waits for the JavaScript variable `trArray` to be available globally within a specified timeout period,
        retrieves its value, and saves it to a JSON file.

        This method repeatedly checks for the presence of the `trArray` variable by executing a JavaScript script
        in the context of the current page. If the variable is found within the timeout period, its value is saved
        to a file named "trArray.json" and returned. If the variable is not found within the timeout period, a
        TimeoutException is raised.

        Returns:
            list: The value of the `trArray` variable if it is found within the timeout period.

        Raises:
            TimeoutException: If the `trArray` variable is not found within the timeout period.
        """
        # wait for trArray variable to be available globally
        timeout = 30  # seconds
        poll_frequency = 1  # seconds
        end_time: float = time.time() + timeout
        while time.time() < end_time:
            try:
                instructions = self.driver.execute_script("return trArray")
                if instructions:
                    json.dump(instructions, open("trArray.json", "w"))
                    return instructions
            except Exception:
                pass
            time.sleep(poll_frequency)
        raise TimeoutException("Timed out waiting for trArray to be available")

    def survey(self) -> list[dict[str, str]]:
        """
        Waits for the "Earn" page to load, filters and processes task data, and saves the cleaned data to a JSON file.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing the cleaned task data.
        """
        while "Earn" not in self.driver.title:
            print("Earn  page yet to be loaded")
            time.sleep(5)
            if self.status=='Working':
                return  []
            
        trA = self.get_tr_data()
        yt_tasks: TrArray = (
            TrArray(trA).filter("Actions", "22").filter("ApprovalRateNumeric", 100)
        )
        grp1: TrArray = yt_tasks.regex_filter(
            "Instructions", "Go to https://t.co/"
        ).regex_filter("Instructions", "i.ytimg.com")
        grp2: TrArray = yt_tasks.regex_filter(
            "Instructions", "https://www.youtube.com/"
        )
        tr_clean: list[dict[str, str]] = grp1.trArray + grp2.trArray
        tra = TrArray(tr_clean)
        tra=tra.sort_by('Bid')
        print(f'found {len(tr_clean)} tasks')
        json.dump(tr_clean, open("tr_clean.json", "w"))
        return tra.trArray
