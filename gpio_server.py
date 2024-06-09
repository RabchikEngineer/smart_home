import os
from bottle import route, run, get, post,request,static_file
import json,random

from gevent import monkey; monkey.patch_all()


if os.environ.get('GPIO_AVAILABLE'):
    import RPi.GPIO as GP
else:
    import repl_gp as GP

GP.setmode(GP.BCM)
# pin=int(os.environ.get('LIGHT_PIN'))
# GP.setup(pin,GP.OUT)

@post('/setup')
def setup():
    print(request.json)
    data=request.json
    GP.setup(data['pin'],getattr(GP,data['mode']))
    return "success"


@post('/output')
def output():
    print(request.json)
    data = request.json
    GP.output(data['pin'], int(data['level']))
    return "success"

@post('/clear')
def output():
    data = request.json
    if data:
        GP.cleanup(data['pins'])
    else:
        GP.cleanup()
    return "success"



with open("config.json", encoding='utf-8') as f:
    config=json.load(f)


run(host=config['host'], port=config['port'], debug=config['debug'], server='gevent')


