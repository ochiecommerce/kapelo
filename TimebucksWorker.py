from random import randint
import os, re, time, pathlib
import pyperclip
from workers import YtTasksSurveyer, random_string, YouTube

from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from utils import EventService, FileService, search_file, search_remote_file

from ke_client import Client
import traceback

from models import ProblematicTask


class TimebucksWorker(YtTasksSurveyer):
    """
    Represents a single worker in timebucks.com
    """

    def __init__(
        self,
        driver: WebDriver = None,
        info_line=print,
        dialog=None,
        file_service:FileService=None
    ):
        """
        Create a new timebucks worker
        """
        super().__init__(
            driver=driver,
        )

        self.last_task_failed = False
        self.total_tasks: int = 0
        self.filtered_tasks = False
        self.stop_flag: bool = False
        self.info_line = info_line
        self.running = False
        self.searching = False
        self.mode = ""
        self.passive = False
        self.wait_time = 30
        self.dialog = dialog
        self.last_campaign_start = 0
        self.current_campaign_id = None
        self.event_service = EventService()
        self.file_service = file_service
        os.makedirs("screenshots", exist_ok=True)
        self.set_locators(
            start_campaign=(By.XPATH, '//*[@id="send"]'),
            file_input=(
                By.ID,
                "SupportFiles",
            ),
            thumbnail_image=(By.XPATH, "/html/body/img"),
            back_to_tasks=(
                By.CSS_SELECTOR,
                ".btn-green.btnBuyTasksBack",
            ),
            see_video_id=(
                By.XPATH,
                "/html/body/div[9]/div[3]/div/div[2]/div[2]/div/div/div[3]/div/div/div[1]/div[5]/div[3]/div[4]/p[2]/a[2]",
            ),
            image_proof=(By.ID, "taskThumbnail"),
            submit_task=(By.CSS_SELECTOR, ".btnSubmitForApproval#send"),
            cancel_campaign=(
                By.CSS_SELECTOR,
                ".btnCancelBuyTasksCampaign#send",
            ),
        )

    def filter_tasks(self):
        if self.status == "Working":
            self.handle_task()
        if self.filtered_tasks:
            self.driver.execute_script(
                """
document.getElementById("buyTasksCampaignTitle").value = "Watch";
document.querySelector(".btnFilterTasks").click()
                """
            )

        else:
            self.driver.execute_script(
                """
document.querySelectorAll('.multiselect')[1].click();
let items = document.querySelectorAll('.dropdown-item');
items[0].click()
items.forEach(item => {
    if (item.innerText.startsWith('Watch')) item.click();
})
document.getElementById("buyTasksCampaignTitle").value = "Watch";
document.querySelector(".btnFilterTasks").click()
                """
            )
            self.filtered_tasks = True

    def next(self):
        self.filter_tasks()
        time.sleep(3)
        tbody = self.driver.find_element(By.CLASS_NAME, "buyTasksBody")
        campaign_rows = tbody.get_property("children")
        if len(campaign_rows) < 1:
            self.driver.execute_script("window.scrollBy(0, -window.innerHeight);")
            time.sleep(3)
            self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
            return self.next()
        for campaign_row in campaign_rows:
            self.scroll_to(campaign_row)
            instructions = campaign_row.get_property("innerText")
            class_name: str = campaign_row.get_attribute("class")
            campaign_id = "".join([x for x in class_name if x.isdigit()])
            if re.search("Watch 1 mins of video", instructions):

                # check if the task is problematic
                problematic_task = ProblematicTask.get_or_none(
                    ProblematicTask.task_id == campaign_id
                )
                if problematic_task:
                    continue
                self.view_task2(campaign_id)

                if self.passive and not self.passively_doable():
                    self.back_to_tasks()
                    continue

                self.start_campaign()
                self.current_campaign_id = campaign_id
                if not self.handle_task():
                    new_problematic_task = ProblematicTask(task_id=campaign_id)
                    new_problematic_task.save()
                    self.hide_campaign(campaign_id)
                    return 0
                return 1

            else:
                self.hide_campaign(campaign_id)
        return 0

    def back_to_tasks(self):
        # back = self.wait_for("back_to_tasks")
        # back.click()
        self.driver.execute_script(
            """document.querySelector(".btn-green.btnBuyTasksBack").click()"""
        )
        


    def passively_doable(self):
        instructions_element = self.wait_for("p.instructions")
        instructions = instructions_element.get_property("innerText")
        urls: list[str] = YouTube.get_urls(instructions)
        vid: str = YouTube.video_id(urls[-1])
        preview = search_file("screenshots", vid)

        if preview:
            print("found a preview", preview)
            return preview
        return False

    def view_task2(self, campId):
        """
        Attempts to find and click a task element with the given campaign ID within a specified timeout period.
        Args:
            campId (str): The campaign ID of the task to be found and clicked.
        Returns:
            bool: True if the task element was found and clicked successfully, False otherwise.
        Behavior:
            - Searches for the task element with the specified campaign ID.
            - If the element is found and has not been clicked before, it clicks the element using JavaScript.
            - If the element has already been clicked, it returns False.
            - If the element is not found within the timeout period, it scrolls down and retries until the timeout expires.
            - If the element is not found within the timeout period and the status is "Working", it calls the handle_task method.
        """

        timeout = 20  # Maximum time to wait for the element
        end_time: float = time.time() + timeout
        while time.time() < end_time:
            try:
                # Try to find the element
                viewCampaign: EC.WebElement = self.driver.find_element(
                    By.CSS_SELECTOR, f".campaignRow{campId} .btnTasksViewCampaign"
                )
                self.random_click(viewCampaign)
                return True
            except Exception:
                # Scroll down and wait for a short period before trying again
                self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(1)
        print(f"Element with campId {campId} not found within the timeout period.")
        if self.status == "Working":
            self.handle_task()
        self.next()
        return False

    def submit_task(self, file_path: str):
        """
        Submit task
        """

        vid = file_path.split("/")[1]
        pyperclip.copy(vid)
        delete_target = vid

        time_taken = time.time() - self.last_campaign_start
        if time_taken < 61:
            time.sleep(61 - time_taken)

        self.event_service.wait_confirmation()
        print("task submitted")
        os.remove("screenshots/" + delete_target)
        return True

    def keyboard_submit(self, file_path: str):
        """
        Submit task using keyboard shortcuts
        """
        vid = file_path.split("/")[1]
        pyperclip.copy(vid)

        def press_key(key: str):
            self.kec.press(key)
            time.sleep(randint(50, 200) / 1000)
            self.kec.release(key)
            time.sleep(randint(1, 3))

        press_key("tab")
        press_key("tab")
        press_key("tab")
        press_key("enter")
        time.sleep(3)
        press_key("a")
        self.kec.press("ctrl")
        time.sleep(0.1)
        press_key("v")
        press_key("a")
        self.kec.release("ctrl")
        press_key("left")
        press_key("delete")
        press_key("enter")
        time.sleep(3)
        time_taken = time.time() - self.last_campaign_start
        if time_taken < 61:
            time.sleep(61 - time_taken)

        os.remove("screenshots/" + vid)
        press_key("tab")
        press_key("tab")
        press_key("tab")
        press_key("enter")
        return True

    def automatic_submit(self, file_path: str):
        done = False
        try:

            addToFavTask: EC.WebElement = self._driver.find_element(
                By.ID, "addToFavTask"
            )
            self.random_click(addToFavTask)
            print("added to fav tasks")
        except Exception:
            pass
        try:
            print("interacting with file input")
            file_input: EC.WebElement = self.wait.until(
                EC.presence_of_element_located(self.locators["file_input"])
            )

            def internal_upload():
                current_dir = pathlib.Path(__file__).parent.absolute()
                abs_path = os.sep.join((str(current_dir), file_path))
                file_input.send_keys(abs_path)

            internal_upload()
            time.sleep(5)
            self.wait.until(
                EC.visibility_of_element_located(self.locators["image_proof"])
            )
            os.remove(file_path)
            print("deleted", file_path)
            submit_task: EC.WebElement = self.wait.until(
                EC.visibility_of_element_located(self.locators["submit_task"])
            )
            try:

                def submit():
                    time_taken = time.time() - self.last_campaign_start
                    if time_taken < 61:
                        time.sleep(61 - time_taken)
                    self.random_click(submit_task)

                    self.wait.until(EC.alert_is_present())
                    self.driver.switch_to.alert.accept()
                    self.total_tasks += 1
                    print("task submitted successfully")
                    return True

                for _ in range(3):
                    try:
                        if submit():
                            done = True
                            break

                    except Exception:
                        traceback.print_exc()
                        print("submission failed,retrying...")

            except Exception:
                traceback.print_exc()
                print("submission failed,retrying...")

        except Exception:
            traceback.print_exc()
            print("task submission failed")

        if not done:
            self.cancel_campaign("task submission failed")

        return done

    def hide_campaign(self, campaignId):
        """
        Hides a campaign by clicking the hide button associated with the given campaign ID.

        Args:
            campaignId (str): The ID of the campaign to hide.

        Returns:
            bool: True if the campaign was successfully hidden, False otherwise.

        Raises:
            Exception: If an error occurs while attempting to hide the campaign.
        """
        try:
            wt = self.wait_time
            self.wait_time /= 2
            hide: EC.WebElement = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f".campaignRow{campaignId} .hideThisTask")
                )
            )
            self.wait_time = wt
            self.random_click(hide)
            print("successfully hidden campaign")
            return True
        except Exception as e:
            print("could not hide campaign", str(e))
            traceback.print_exc()
            return False

    def cancel_campaign(self, reason):
        """
        Cancel campaign with the given reason
        """

        try:
            self._driver.switch_to.window(self.main_window)
            cancel: EC.WebElement = self.wait_for("cancel_campaign")
            self.random_click(cancel)
            Alert(self._driver).accept()

            print(f"successfully cancelled campaign because {reason}")
            return True
        except (
            StaleElementReferenceException,
            ElementClickInterceptedException,
            TimeoutException,
        ):
            self.repair()

        except Exception as e:
            print("could not cancel campaign", str(e))
            traceback.print_exc()
            return False

    def start_campaign(self) -> bool:
        """
        Clicks the start campain button to start a task
        """
        print("starting campaign")
        self.last_campaign_start = time.time()

        try:
            start_button: EC.WebElement = self.wait_for("start_campaign")
            self.random_click(start_button)

            return True
        except TimeoutException:
            back_to_tasks: EC.WebElement = self.driver.find_element(
                *self.locators["back_to_tasks"]
            )
            self.random_click(back_to_tasks)
            print("Campaign not started")
            return False

    def do_task(self, task: str) -> str | bool:  # pragma: no cover
        """
        Handles a single task of watching youtube video
        """
        raise NotImplementedError("This method must be implemented by a subclass")

    def handle_tasks(self) -> int:
        """
        Opens the tasks tab to handle the tasks that involve watching youtube videos
        """
        print("handling tasks")
        time.sleep(10)
        self.filter_tasks()

        tasks: list[dict[str, str]] = []
        try:
            tasks = self.survey()
        except:
            pass
        if len(tasks) < 1:
            self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
            return self.next()

        for id, task in enumerate(tasks):
            if True:
                print("waiting for full page load")
                time.sleep(5)
                if self.status == "Searching":

                    # check if the task is problematic
                    problematic_task = ProblematicTask.get_or_none(
                        ProblematicTask.task_id == task["Id"]
                    )
                    if problematic_task:
                        print(f"Task {task['Id']} is problematic, skipping")
                        continue
                    if self.view_task2(task["Id"]):
                        try:
                            done = False
                            if self.start_campaign():
                                print("task started")
                                self.current_campaign_id = task["Id"]
                                done: str | bool = self.do_task(task["Instructions"])

                            if done:
                                print(f"submitting {done}")
                                self.submit_task(done)
                            else:
                                print("task failed")
                                time.sleep(5)
                                self.hide_campaign(task["Id"])
                                return id
                        except Exception:
                            traceback.print_exc()

                elif self.status == "Working":
                    self.handle_task()

                else:
                    raise RuntimeError("unknown worker status")

        return len(tasks)

    def handle_task(self):
        """
        Handles a single task of watching youtube video
        """

        p_instructions: EC.WebElement = self.driver.find_element(
            By.CLASS_NAME, "instructions"
        )
        # get the textContent of the element
        instructions: str | None = p_instructions.get_attribute("textContent")
        done: str | bool = self.do_task(instructions)
        print("task done")
        if done:
            return self.submit_task(done)

        else:
            self.cancel_campaign("task failed")
            return False

    def _work(self) -> None:
        while True:
            if self.status == "Searching":
                try:
                    # if self.handle_tasks()==0:
                    #    return
                    self.next()
                except:
                    traceback.print_exc()
                    return

            elif self.status == "Working":
                self.handle_task()

    def work(self) -> None:
        """
        Start the work thread of the worker
        """
        self._work()

    def stop(self) -> None:
        """
        Stops the worker by setting the running flag to False and waiting for the work thread to terminate
        """
        if self.running:
            self.running = False
            self.thread.join()
            print("successfully stopped worker")


class LocalTBWorker(TimebucksWorker):
    """
    LocalTBWorker is a subclass of TimebucksWorker that handles tasks related to watching YouTube videos localy.
        Methods:
            do_task(task: str) -> str | None:
                Handles a single task of watching a YouTube video. Opens a new tab, takes a screenshot, and closes the tab after the task is completed. Returns the path to the screenshot if successful, None if the task fails, and False if an error occurs.
    """

    def do_task(self, task: str) -> str | None:
        """
        Handles a single task of watching youtube video
        """
        print("opening new tab for watching video")
        urls: list[str] = YouTube.get_urls(task)
        vid: str = YouTube.video_id(urls[-1])
        preview = search_file("screenshots", vid)

        if preview:
            print("found a preview", preview)
            return preview
        new_tab: str = self.open_new_tab()
        try:
            self.driver.switch_to.window(new_tab)
            yt_slave = YouTube(self.driver)

            if result := yt_slave.do_task(task):
                self.close_tab(new_tab)
                return result

            else:
                print("closing tab after error occured in watching video")
                self.close_tab(new_tab)
                return None

        except Exception as e:
            print("error occured in watching video", str(e))
            traceback.print_exc()
            self.close_tab(new_tab)
            self.cancel_campaign("error occured in watching video")
            return False


class RemoteTBWorker(TimebucksWorker):
    """
    RemoteTBWorker is a subclass of TimebucksWorker that handles tasks related to watching YouTube videos remotely.
    Methods:
        do_task(task: str):
            Handles a single task of watching a YouTube video. Takes a task description as input and returns the path to the screenshot taken during the task. If an error occurs, it prints an error message, cancels the campaign, and raises the exception.
    """

    def __init__(self, driver=None, info_line=print, dialog=None, yt_server=None):
        super().__init__(driver, info_line, dialog)
        self.yt_server = yt_server

    def do_task(self, task: str):
        """
        Handles a single task of watching youtube video
        """

        urls: list[str] = YouTube.get_urls(task)
        vid: str = YouTube.video_id(urls[-1])
        preview = search_remote_file(self.yt_server, vid)

        if preview:
            print("found a preview", preview)
            return preview
