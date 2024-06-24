import json

import requests

from dependencies import config


class Device:
    id: int
    pin: int
    name: str
    level: int
    server_url = f'http://{config["gpio_server_ip"]}:{config["gpio_server_port"]}/'

    def __init__(self, pin, name="", image=None):
        self.pin = pin
        self.name = name
        self.level = 0
        self.image = image
        self.update()

    def toggle(self):
        level=1-self.level
        res=requests.post(self.server_url+'output',json={'pin':self.pin, 'level':level, 'auto':1})
        if res.status_code==requests.codes.OK:
            self.level = level
            return level
        return res

    def set(self,level):
        res = requests.post(self.server_url + 'output', json={'pin': self.pin, 'level': level, 'auto': 1})
        if res.status_code == requests.codes.OK:
            self.level = level
            return level
        return res

    def update(self):
        self.level=self.status()['level']

    def status(self):
        res=requests.get(self.server_url+'status',json={'pin':self.pin,'auto':1})
        if res.status_code==requests.codes.OK:
            return res.json()
        return res



