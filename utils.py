import requests
import re
import os

import tkinter as tk

def choose(options:list,title:str="Choose an option"):
    window = tk.Tk()
    window.withdraw()
    dialog = tk.Toplevel(window)
    dialog.title(title)
    dialog.geometry('300x150')

    choice = tk.StringVar()

    def on_select(opt):
        choice.set(opt)
        dialog.destroy()

    for opt in options:
        rb = tk.Radiobutton(dialog, text=opt, variable=choice, value=choice, command=lambda opt=opt:on_select(opt))
        rb.pack()

    dialog.wait_window()
    return choice.get()


SERVER_HOST = os.getenv("SERVER_HOST")



def get_urls(text):
    # Regular expression pattern to match URLs
    url_pattern = r"https?://[^\s]+"

    # Find all URLs in the text
    urls = re.findall(url_pattern, text)

    return urls


def video_id(url):
    # Regular expression to extract the video ID
    pattern = r"https://i\.ytimg\.com/vi/([^/]+)/[a-z]+\.jpg"

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


class RemoteYouTube:
    def __init__(self):
        self.client = requests.sessions.Session()
        self.screenshot = "image.png"

    def do_task(self, instructions: str):
        task: dict[str, str] = {"Instructions": instructions}
        print("Sending Task:", task)
        res: requests.Response = self.client.post(
            f"http://{SERVER_HOST}:8484/get_submission", json=task, timeout=150
        )
        downld = res.content
        kb: float = len(downld) / 1024
        print("Downloaded:", kb, "KB")
        if kb < 4:
            print("Error:", downld)
            return False
        file = open(self.screenshot, "wb")
        file.write(downld)
        return True


def search_file(folder,prefix):
    '''search for a file whose name begins with a given string'''
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.startswith(prefix):
                return os.path.join(root, file)
                
def search_files(folder,prefix):
    '''search for files whose name begins with a given string'''
    found_files=[]
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.startswith(prefix):
                found_files.append(os.path.join(root, file))
    return found_files

        
