import socket as so, time
from threading import Thread
class Client:
    def __init__(self):
        client = so.socket(so.AF_INET,so.SOCK_STREAM)
        client.connect(('',6566))
        self.client = client
        self.running = False
        self.handlers = []
        self.thread = None
        self._latest_event = None

    @property
    def latest_event(self):
        le = self._latest_event
        self._latest_event = None
        return le
        
    def _run(self):
        while self.running:
            event_name = self.client.recv(8).decode()
            for handler in self.handlers:
                handler(event_name)

    def stop(self):
        self.running = False
        self.thread.join()

    def start(self):
        self.thread = Thread(target=self._run)
        self.running = True
        self.thread.start()

    def _wait_handler(self,event_name):
        self._latest_event = event_name

    def add_handler(self,handler):
        self.handlers.append(handler)

    def wait_for(self, event_name):
        self.handlers.append(self._wait_handler)
        while True:
            if self.latest_event == event_name:
                self.handlers.remove(self._wait_handler)
                return
        
