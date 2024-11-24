import os, sys
import json, random

from loguru import logger

from bottle import route, run, Bottle, request, static_file, response
from gevent import monkey;

if os.environ.get('GPIO_AVAILABLE'):
    import RPi.GPIO as GP
else:
    import repl_gp as GP

monkey.patch_all()


with open("../config.json", encoding='utf-8') as f:
    config = json.load(f)


class Pin:
    level = 0

    # init and setup of the pin, if mode given
    def __init__(self, n, mode=None):
        self.n = n
        self.mode = mode
        if mode is not None:
            self.setup(mode)

    # setup pin on given mode, if not given, takes from Pin object
    def setup(self, mode=None):
        if mode is None:
            mode = self.mode
        GP.setup(self.n, mode)
        self.mode = mode

    def output(self, level):
        GP.output(self.n, level)
        self.level = level

    def input(self) -> float:
        return GP.input(self.n)


class PinSet:
    pins: dict[int, Pin] = {}
    mode = None

    def __init__(self):
        pass

    def setmode(self, mode=GP.BCM):
        GP.setmode(mode)
        self.mode = mode
        logger.info(f'Set pinset mode {mode}')

    # add pin to dict of pins
    def add_pin(self, pin) -> Pin:
        self.pins.update({pin.n: pin})
        return pin

    # check, is pin ready to be operated
    def check(self, n, mode=None) -> str | bool:
        if not GP.getmode(): return "setmode"
        if not self.pins.get(n): return "create"
        if (mode is not None) and self.pins[n].mode != mode: return "setup"
        return True

    # configure pins
    def auto_config(self, n, mode=None):
        while self.check(n, mode) != True:
            logger.info(f'Auto-configured {n} pin to {mode}')
            match self.check(n, mode):
                case "setmode":
                    self.setmode()
                case "create":
                    self.add_pin(Pin(n, mode))
                case "setup":
                    self.pins[n].setup(mode)


    def output(self, n, level):
        self.pins[n].output(level)
        logger.success(f'Set output level to {level} on {n} pin')

    def input(self, n: int):
        logger.success(f'Get input level to {level} on {n} pin')
        return self.pins[n].input()


    def get_pin(self, n: int):
        return self.pins[n]


def internal_error_handler(error):
    logger.error({"error": error.args[2].__repr__(), "traceback": error.traceback})
    return json.dumps({"error": error.args[2].__repr__(), "traceback": error.traceback})


log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
logger.remove()
logger.add("log.txt", level=2, format=log_format)
logger.add(sys.stdout, level=10, format=log_format)

app = Bottle()
app.error_handler.update({500: internal_error_handler})
response.default_content_type = "application/json"

pinset = PinSet()


@app.post('/setmode')
def setmode():
    data = request.json
    pinset.setmode(data['mode'])


@app.post('/setup')
def setup():
    data = request.json
    pinset.auto_config(data['pin'], getattr(GP, data['mode'].upper()))


@app.post('/output')
def output():
    data = request.json
    if data.get('auto'):
        pinset.auto_config(data['pin'], GP.OUT)
    pinset.output(data['pin'], data['level'])


@app.get('/input')
def inp():
    data = request.json
    if data.get('auto'):
        pinset.auto_config(data['pin'], GP.IN)
    return json.dumps({"level": pinset.input(data['pin'])})


@app.get('/status')
def status():
    data = request.json
    if data.get('auto'):
        pinset.auto_config(data['pin'])
    pin = pinset.get_pin(data['pin'])
    return json.dumps({"mode": pin.mode, 'level': pin.level})


@app.post('/clear')
def handler():
    data = request.json
    if data:
        GP.cleanup(data['pins'])
    else:
        GP.cleanup()



run(app, host=config['gpio']['host'], port=config['gpio']['port'], debug=config['gpio']['debug'], server='gevent')
