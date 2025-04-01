import os
import pathlib
from selenium.webdriver.chrome.webdriver import WebDriver
from drivers import chrome, firefox
from TimebucksWorker import LocalTBWorker, time
from args import args
import time

working_directory: str = os.getcwd()
if args.wd:
    working_directory = args.wd
else:
    print("No working directory specified, using current directory",working_directory)
os.chdir(working_directory)

profiles: list[str] = []

if args.p:
    profiles = [f'Profile {p}' for p in args.p]

else:
    profiles = ['Profile 1']

while True:
    for profile in profiles:
        driver = chrome(profile)

        worker = LocalTBWorker(driver)
        time.sleep(5)

        if args.s:
            worker.set_data(profile)
            worker.driver.refresh()
            worker.initialize()
            
        time.sleep(5)
        worker.work()

        
