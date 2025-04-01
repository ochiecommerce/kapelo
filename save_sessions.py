from selenium.webdriver.chrome.webdriver import WebDriver
from session_utils import TimeDelta
from ads_lib import profiles
from drivers import chrome
from session_utils import Session


def save(profile):
    driver: WebDriver = chrome(profile)
    session = Session(
        driver,
        "https://timebucks.com/publishers/index.php?pg=earn&tab=tasks_tasks")
    session.save_data(profile, extend_cookies=TimeDelta(days=30))
    driver.quit()
    print("saved session for", profile)


def load(profile):
    driver: WebDriver = chrome(profile)
    session = Session(
        driver,
        page="https://timebucks.com/publishers/index.php?pg=earn&tab=tasks_tasks",
    )
    session.clear_data()
    session.set_data(profile)
    print("loaded data for", profile)


def save_all():
    for profile in profiles:
        save(profile)


def load_all():
    for profile in profiles:
        load(profile)
