#!/usr/bin/env python3

import os, time
from selenium.webdriver.chrome.webdriver import WebDriver
from drivers import chrome, firefox
from TimebucksWorker import LocalTBWorker, time
from args import args
from utils import FileService, serve_screenshots

working_directory: str = os.getcwd()
if args.wd:
    working_directory = args.wd
else:
    print("No working directory specified, using current directory", working_directory)
os.chdir(working_directory)

profiles: list[str] = []

if args.p:
    profiles = [f"Profile {p}" for p in args.p]

else:
    profiles = ["Profile 1"]

fs = "http://localhost:5000"

if not args.fs:
    serve_screenshots()

else:
    fs = args.fs

while True:
    for profile in profiles:
        driver = chrome(profile)
        FileService.register(fs, profile, profile)
        file_service = FileService(fs, profile, profile)
        worker = LocalTBWorker(driver, file_service=file_service)
        time.sleep(5)

        if args.s:
            worker.set_data(profile)
            worker.driver.refresh()
            worker.initialize()

        if args.ps:
            worker.passive = True

        time.sleep(5)
        worker.work()
