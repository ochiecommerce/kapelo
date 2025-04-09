import os, re, requests, tkinter as tk
from threading import Thread
from tkinter import messagebox
from bs4 import BeautifulSoup
from ke_client import Client
from time import time


def console_choose(options: list):
    print("reply with:")
    for i, option in enumerate(options):
        print(f"{i+1}: {option}")
    choice = input()
    if not choice.isdigit():
        return console_choose(options)
    if not len(options) + 1 >= choice >= 1:
        return console_choose(options)

    return options[choice - 1]


def choose(options: list, title: str = "Choose an option"):
    if tk:
        window = tk.Tk()
        window.withdraw()
        dialog = tk.Toplevel(window)
        dialog.title(title)
        dialog.geometry("300x150")

        choice = tk.StringVar()

        def on_select(opt):
            choice.set(opt)
            dialog.destroy()

        for opt in options:
            rb = tk.Radiobutton(
                dialog,
                text=opt,
                variable=choice,
                value=choice,
                command=lambda opt=opt: on_select(opt),
            )
            rb.pack()

        dialog.wait_window()
        return choice.get()

    else:
        print(title)
        return console_choose(options)


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
    vid = None
    if match:
        vid = match.group(1)
        print(f"Video ID: {vid}")
    else:
        print(f"No video ID found in {url}")

    return vid



def search_file(folder, prefix):
    """search for a file whose name begins with a given string"""
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.startswith(prefix):
                return os.path.join(root, file)
            

def search_files(folder, prefix):
    """search for a file whose name begins with a given string"""
    files_found = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.startswith(prefix):
                files_found.append(file)
    
    return files_found


def search_remote_file(server_link, prefix):
    req = requests.get(server_link, timeout=60)
    bs = BeautifulSoup(req.content, "html.parser")
    links: list[str] = [a.get("href") for a in bs.find_all("a")]

    submitted_files = SubmittedFile.select()
    for link in links:
        if link.startswith(prefix):
            if submitted_files.where(SubmittedFile.name == link).exists():
                continue
            submitted_file = SubmittedFile(name=link)
            submitted_file.save()
            return server_link + link
        
def confirm(title='Confirmation',message='Press ok to continue'):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title,message)
    root.destroy()


class EventService:
    def __init__(self):
        try:
            self.kec = Client()
            self.kec.start()
            self.mode = 'kes'
        except:
            print('could not connect to keyboard event server')
            self.mode = 'tes'

    def wait_confirmation(self):
        if self.mode == 'kes':
            return self.kec.wait_for('n')
        
        else:
            confirm()


class FileService:
    @staticmethod
    def register(server,username,password):
        req=requests.post(server+'/register',data={'username':username,'password':password}, timeout=60)
        return req.ok
    
    def __init__(self, server, username,passwd):
        self.session = requests.Session()
        self.session.post(server+'/login',data={'username':username,'password':passwd})
        self.server = server

    def get_file(self,vid):
        response=self.session.get(self.server+'/search_file',params={'folder':'screenshots','prefix':vid})
        if response.status_code==200:
            return response.text
        
    def download(self,file_name):
        response = self.session.get(self.server+'/download', params={'file':file_name}, timeout=60)
        if response.ok:
            file_name = str(time())+'.png'
            file = open(file_name,'wb')
            file.write(response.content)


def serve_screenshots():
    from files_server import  app
    def server():
        app.run(
            host='0.0.0.0'
        )

    thread = Thread(target=server)
    thread.start()

