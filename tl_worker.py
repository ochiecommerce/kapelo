#!/usr/bin/env python3

import os, time
from drivers import chrome
from TimebucksWorker import TimebucksWorker
from args import args
from utils import FileService, serve_screenshots

working_directory: str = os.getcwd()
if args.wd:
    working_directory = args.wd
else:
    print("No working directory specified, using current directory", working_directory)
os.chdir(working_directory)
os.makedirs('screenshots', exist_ok=True)
os.makedirs('submissions', exist_ok=True)

profiles: list[str] = []

if args.p:
    profiles = [f"Profile {p}" for p in args.p]

else:
    profiles = ["Profile 1"]

fs = 'http://localhost:5000'

if not args.fs:
    serve_screenshots()

else:
    fs = args.fs

while True:
    for profile in profiles:
        driver = chrome(profile)
        FileService.register(fs,profile,profile)
        files = FileService(fs,profile,profile)
        worker = TimebucksWorker(driver, file_service=files)
        time.sleep(5)
        
        if args.s:
            worker.set_data(profile)
            worker.driver.refresh()
            worker.initialize()

        if args.ps:
            worker.passive = True

        time.sleep(5)
        worker.work()
