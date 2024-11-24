import requests
import json
import os

pos=os.getcwd().rfind('event_handlers')
if pos>0:
    os.chdir(os.getcwd()[:pos])
# print(os.getcwd())
with open("../config.json", encoding='utf-8') as f:
    config = json.load(f)



class Device:
    id: int
    pin: int
    name: str
    level: int
    server_url = f'http://{config["gpio"]["server_ip"]}:{config["gpio"]["port"]}/'

    def __init__(self, pin):
        self.pin = pin
        self.level = 0
        self.update()

    def request_server(self, method, url, json):
        res = requests.request(method=method, url=self.server_url + url, json=json)
        if res.status_code != requests.codes.OK:
            pass # logger error
        return res

    def toggle(self):
        level = 1 - self.level
        res = self.request_server('post','output', json={'pin': self.pin, 'level': level, 'auto': 1})
        self.level = level
        return level

    def set(self, level):
        res = self.request_server('post','output', json={'pin': self.pin, 'level': level, 'auto': 1})
        self.level = level
        return level

    def update(self):
        status = self.status()
        self.level = status['level']

    def status(self):
        res = self.request_server('get','status', json={'pin': self.pin, 'auto': 1})
        return res.json()


