import os
from bottle import route,run, Bottle,request,static_file,response
import json,random

from gevent import monkey; monkey.patch_all()


if os.environ.get('GPIO_AVAILABLE'):
    import RPi.GPIO as GP
else:
    import repl_gp as GP


class PinSet:

    pins={}
    mode=None

    def __init__(self):
        pass

    def setmode(self,mode=GP.BCM):
        GP.setmode(mode)
        self.mode = mode

    def add_pin(self, pin):
        self.pins.update({pin.n:pin})
        return pin

    def check(self,n,mode=None):
        if not GP.getmode(): return "setmode"
        if not self.pins.get(n): return "create"
        if (mode is not None) and self.pins[n].mode != mode: return "setup"
        return True

    def auto_config(self,n,mode):
        while self.check(n,mode) != True:
            match self.check(n,mode):
                case "setmode":
                    self.setmode()
                case "create":
                    self.add_pin(Pin(n,mode))
                case "setup":
                    self.pins[n].setup(mode)

    def output(self,n,value):
        self.pins[n].output(value)

    def input(self,n):
        return self.pins[n].input()


class Pin:

    def __init__(self, n, mode=None):
        self.n = n
        if mode is not None:
            self.mode = mode
            self.setup(mode)

    def setup(self,mode=None):
        if mode is None:
            mode=self.mode
        GP.setup(self.n, mode)
        self.mode=mode

    def output(self, value):
        GP.output(self.n, value)

    def input(self):
        return GP.input(self.n)


def internal_error_handler(error):
    # print(error)
    # print(dir(error))
    # print(error.body)
    response.content_type="application/json"
    return json.dumps({"error":error.args[2].__repr__(),"traceback":error.traceback})

app=Bottle()
app.error_handler={500: internal_error_handler}


pinset=PinSet()


@app.post('/setmode')
def handler():
    data = request.json
    pinset.setmode(data['mode'])


@app.post('/setup')
def handler():
    data=request.json
    pinset.auto_config(data['pin'],getattr(GP,data['mode'].upper()))


@app.post('/output')
def handler():
    data = request.json
    if data.get('auto'):
        pinset.auto_config(data['pin'],GP.OUT)
    pinset.output(data['pin'], data['level'])


@app.get('/input')
def handler():
    data = request.json
    if data.get('auto'):
        pinset.auto_config(data['pin'], GP.IN)
    return json.dumps({"level":pinset.input(data['pin'])})


@app.post('/clear')
def handler():
    data = request.json
    if data:
        GP.cleanup(data['pins'])
    else:
        GP.cleanup()



with open("config.json", encoding='utf-8') as f:
    config=json.load(f)


run(app,host=config['host'], port=config['port'], debug=config['debug'], server='gevent')


