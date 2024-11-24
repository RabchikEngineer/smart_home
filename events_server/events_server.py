import os, sys
import json, random, json_fix
import threading as th
import time
import requests
from loguru import logger

from bottle import route, run, Bottle, request, response
from gevent import monkey

monkey.patch_all()

event_file_path='events.json'

with open("../config.json", encoding='utf-8') as f:
    config = json.load(f)

log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
# logger.level("TEXT", no=22, color="<blue>", icon="T")
logger.remove()
logger.add("log.txt", level=2, format=log_format)
logger.add(sys.stdout, level=10, format=log_format)


class Event():

    target: str
    action: str
    time: float
    expiration_time: float

    no_events_lock=th.Lock()
    events: list['Event'] = []

    @classmethod
    def load_events(cls):
        with open(event_file_path, encoding='utf-8') as f:
            data=json.load(f)
            for event in data:
                Event(**event)
        if not cls.events:
            cls.no_events_lock.acquire()

    @classmethod
    def save_events(cls):
        with open(event_file_path, 'w', encoding='utf-8') as f:
            json.dump(cls.events, f, indent=4)

    @classmethod
    def get_event(cls) -> 'Event':
        ev=cls.events.pop(0)
        if not cls.events:
            cls.no_events_lock.acquire()
        return ev

    def __init__(self, target, action, time, expiration_time):
        self.target = target
        self.action = action
        self.time = time
        self.expiration_time = expiration_time
        self.events.append(self)
        if self.no_events_lock.locked():
            self.no_events_lock.release()

    def __json__(self):
        return self.__dict__

    def __repr__(self):
        return json.dumps(self.__json__())





try:
    Event.load_events()
except:
    raise Exception('Failed to load events, check file')


def event_handler():
    while True:
        Event.no_events_lock.acquire()
        Event.no_events_lock.release()
        ev=Event.get_event()
        Event.save_events()

        path=f'event_handlers/{ev.target}/{ev.action}.py'
        if os.path.exists(path):
            with (open(path) as f):
                data = f.read().replace('events_server.', ''
                                        ).replace('config.json',f'event_handlers/{ev.target}/config.json')
                try:
                    exec(data)
                    logger.success(f"succesfully executed {ev.target}:{ev.action}")
                except:
                    logger.error(f"error in module {path}")
        else:
            logger.info(f"handler {path} not found")


        time.sleep(5)



events_handler_thread = th.Thread(target=event_handler, daemon=True)
events_handler_thread.start()


def internal_error_handler(error):
    return json.dumps({"error": error.args[2].__repr__(), "traceback": error.traceback})


app = Bottle()
# app.error_handler.update({500: internal_error_handler})
response.default_content_type = "application/json"



@app.get('/get')
def setup():
    if Event.no_events_lock.locked():
        response.status=418
        return None
    ev = Event.get_event()
    Event.save_events()
    return json.dumps(ev)

@app.post('/add')
def output():
    data = request.json
    # remove prohibited symbols
    data['target']=data['target'].replace(' ','_')
    Event(target=data['target'], action=data['action'], time=data['time'],expiration_time=data['expiration_time'])
    Event.save_events()


run(app, host=config['events']['host'], port=config['events']['port'], debug=config['events']['debug'],
        server='gevent')


