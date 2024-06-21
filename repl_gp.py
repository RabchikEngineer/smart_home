import random
OUT = "OUT"
IN = "IN"
BCM = "BCM"
BOARD = "BOARD "


def output(*args):
    print(f'set {args[1]} to {args[0]} pin')


def input(*args):
    return random.random()


def setmode(*args):
    print(f'set mode to {args[0]}')

def getmode():
    return random.randint(10,11)

def setup(*args):
    print(f'set {args[1]} mode to {args[0]} pin')


def cleanup(*args):
    if args:
        print(f'cleaning up {args[0]} pins')
    else:
        print('cleaning up')
