import os
from bottle import route,run, Bottle,request,static_file
import json,random

from gevent import monkey; monkey.patch_all()


if os.environ.get('GPIO_AVAILABLE'):
    import RPi.GPIO as GP
else:
    import repl_gp as GP

GP.setmode(GP.BCM)
# pin=int(os.environ.get('LIGHT_PIN'))
# GP.setup(pin,GP.OUT)

def internal_error_handler(error):
    # print(error)
    # print(dir(error))
    # print(error.body)
    return json.dumps({"error":error.args[2].__repr__(),"traceback":error.traceback})

app=Bottle()
app.error_handler={500: internal_error_handler}


@app.post('/setup')
def setup():
    # print(request.json)
    data=request.json
    GP.setup(data['pin'],getattr(GP,data['mode']))


@app.post('/output')
def output():
    # print(request.json)
    data = request.json
    GP.output(data['pin'], int(data['level']))


@app.get('/input')
def output():
    # print(request.json)
    data = request.json
    return GP.input(data['pin'])


@app.post('/clear')
def clear():
    data = request.json
    if data:
        GP.cleanup(data['pins'])
    else:
        GP.cleanup()



with open("config.json", encoding='utf-8') as f:
    config=json.load(f)


run(app,host=config['host'], port=config['port'], debug=config['debug'], server='gevent')


