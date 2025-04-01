import json
from math import e
import os

from selenium.webdriver.remote.webdriver import WebDriver


class TimeDelta:
    def __init__(
        self, seconds=0.0, minutes=0.0, hours=0.0, days=0.0, weeks=0.0, months=0.0
    ) -> None:
        self.secs: float = seconds
        self.mins: float = minutes
        self.hrs: float = hours
        self.dys: float = days
        self.wks: float = weeks
        self.mths: float = months

    @property
    def seconds(self) -> float:
        return self.secs + 60 * self.mins + 3600 * self.hrs + self.dys * 24 * 60 * 60

    @property
    def minutes(self) -> float:
        return self.seconds / 60

    @property
    def hours(self) -> float:
        return self.minutes / 60

    @property
    def days(self) -> float:
        return self.hours / 24

    @property
    def weeks(self) -> float:
        return self.days / 7


def extend_cookie_lifetime(
    cookies,
    timedelta: TimeDelta,
    name=None,
):
    for cookie in cookies:
        if name:
            if cookie["name"] == name:
                cookie["expiry"] = cookie["expiry"] + timedelta.seconds
                break

        if "expiry" in cookie.keys():
            cookie["expiry"] = cookie["expiry"] + timedelta.seconds
        else:
            print("could not extend", cookie)

    return cookies


def extend1month(file) -> None:
    cookies: dict = json.load(
        open(file, "r+"),
    )
    cookies = extend_cookie_lifetime(cookies, TimeDelta(days=30))
    json.dump(cookies, open(file, "w+"))


class SerializableMixin:
    """
    SerializableMixin is a mixin class that provides methods to save, load, and clear browser session data including cookies, local storage, and session storage.
    Methods:
        save_data(folder: str, extend_cookies: TimeDelta = None) -> str:
        set_data(folder: str) -> None:
            Loads the browser session data including cookies, local storage, and session storage from the specified folder.
                folder (str): The directory where the session data files are located.
                None
        clear_data() -> None:
            Clears all site data including cookies, local storage, and session storage.
                None
    """

    def save_data(self, folder: str, extend_cookies: TimeDelta = None) -> str:
        """
        Saves the browser session data including cookies, local storage, and session storage to the specified folder.
        Args:
            folder (str): The directory where the session data files will be saved.
            extend_cookies (TimeDelta, optional): The time delta to extend the cookie lifetime. Defaults to None.
        Returns:
            str: A JSON string containing the file paths of the saved cookies, local storage, and session storage.
        """

        # Extract cookies
        cookies = self.driver.get_cookies()
        if extend_cookies:
            cookies = extend_cookie_lifetime(cookies, extend_cookies)

        def file_name(file):
            return os.sep.join((folder, f"{file}.json"))

        cookie_file: str = file_name("cookies")
        os.makedirs(folder, exist_ok=True)
        try:
            os.remove(cookie_file)
        except FileNotFoundError:
            pass
        with open(cookie_file, "x+") as file:
            json.dump(cookies, file, indent=4)

        # Extract Local Storage
        local_storage = self.driver.execute_script(
            "return JSON.stringify(localStorage);"
        )
        ls_file = file_name("local_storage")
        try:
            os.remove(ls_file)
        except FileNotFoundError:
            pass
        with open(ls_file, "x+") as file:
            file.write(local_storage)

        # Extract Session Storage
        ss_file = file_name("session_storage")
        try:
            os.remove(ss_file)
        except FileNotFoundError:
            pass
        session_storage = self.driver.execute_script(
            "return JSON.stringify(sessionStorage);"
        )
        with open(ss_file, "x+") as file:
            file.write(session_storage)

        return f'{{"cookies": "{cookies}","local_storage": "{local_storage}","session_storage": "{session_storage}"}}'

    def set_data(self, folder) -> None:
        """
        Loads cookies, local storage, and session storage data from the specified folder
        and sets them in the Firefox driver.
        Args:
            folder (str): The path to the folder containing the data files.
        Raises:
            FileNotFoundError: If any of the data files (cookies.json, local_storage.json,
                               session_storage.json) are not found in the specified folder.
        Side Effects:
            - Clears existing cookies, local storage, and session storage in the Firefox driver.
            - Loads cookies from cookies.json and adds them to the Firefox driver.
            - Loads local storage data from local_storage.json and sets it in the Firefox driver.
            - Loads session storage data from session_storage.json and sets it in the Firefox driver.
        Prints:
            - "✅ Cookies loaded into Firefox." if cookies are successfully loaded.
            - "⚠ No cookies found!" if cookies.json is not found.
            - "✅ Local Storage restored in Firefox." if local storage data is successfully loaded.
            - "⚠ No Local Storage found!" if local_storage.json is not found.
            - "✅ Session Storage restored in Firefox." if session storage data is successfully loaded.
            - "⚠ No Session Storage found!" if session_storage.json is not found.
        """
        self.clear_data()

        # Load cookies
        try:
            with open(os.sep.join((folder, "cookies.json")), "r") as file:
                cookies = json.load(file)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            print("✅ Cookies loaded into Firefox.")
        except FileNotFoundError:
            print("⚠ No cookies found!")

        # Load Local Storage
        try:
            with open(os.sep.join((folder, "local_storage.json")), "r") as file:
                local_storage_data = file.read()
                self.driver.execute_script(
                    f"localStorage.clear(); localStorage = Object.assign(localStorage, {local_storage_data});"
                )
            print("✅ Local Storage restored in Firefox.")
        except FileNotFoundError:
            print("⚠ No Local Storage found!")

        # Load Session Storage
        try:
            with open(os.sep.join((folder, "session_storage.json")), "r") as file:
                session_storage_data = file.read()
                self.driver.execute_script(
                    f"sessionStorage.clear(); sessionStorage = Object.assign(sessionStorage, {session_storage_data});"
                )
            print("✅ Session Storage restored in Firefox.")
        except FileNotFoundError:
            print("⚠ No Session Storage found!")

    def set_from_remote(self, url, profile):
        """
        set cookies from remote url
        the remote sever should return a json object with:
            key "cookies" containing the cookies
            key "local_storage" containing the local storage
            key "session_storage" containing the session storage
        """
        import requests

        data = requests.post(url, json={"profile": profile}).json()
        cookies = data["cookies"]
        local_storage = data["local_storage"]
        session_storage = data["session_storage"]

        for cookie in cookies:
            self.driver.add_cookie(cookie)

        self.driver.execute_script(
            f"localStorage.clear(); localStorage = Object.assign(localStorage, {local_storage});"
        )

        self.driver.execute_script(
            f"sessionStorage.clear(); sessionStorage = Object.assign(sessionStorage, {session_storage});"
        )

    def clear_data(self):
        """clear all site data"""
        # Clear cookies
        self.driver.delete_all_cookies()

        # Clear localStorage
        self.driver.execute_script("window.localStorage.clear();")

        # Clear sessionStorage
        self.driver.execute_script("window.sessionStorage.clear();")


class Session(SerializableMixin):
    """
    A class used to represent a browser session.

    Attributes
    ----------
    driver : WebDriver
        The WebDriver instance used to control the browser.
    page : str
        The URL of the page to be opened.

    Methods
    -------
    __init__(driver: WebDriver, page: str)
        Initializes the session with the given WebDriver and opens the specified page.
    """

    def __init__(self, driver: WebDriver, page):
        self.driver: WebDriver = driver
        self.driver.get(page)
