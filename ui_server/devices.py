import json
import requests

from fastapi import HTTPException

from dependencies import config


class GpioServerError(HTTPException):
    def __init__(self, status_code,detail):
        # super().__init__(418, detail)
        super().__init__(status_code, detail)


class Device:
    id: int
    pin: int
    name: str
    level: int
    server_url = f'http://{config["gpio"]["server_ip"]}:{config["gpio"]["port"]}/'

    def __init__(self, pin, name="", image=None):
        self.pin = pin
        self.name = name
        self.level = 0
        self.image = image
        self.update()

    def request_server(self, method, url, json):
        res = requests.request(method=method, url=self.server_url + url, json=json)
        if res.status_code != requests.codes.OK:
            raise GpioServerError(status_code=res.status_code, detail=res.text)
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
