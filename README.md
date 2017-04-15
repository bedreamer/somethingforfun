# somethingforfun
for fun

TinyHttpServer.py
==============
Usage:
 
from TinyHttpServer import *

def list_root(path, request, ack):
    if 'ok' in ack.user:
        return {'done': True, 'body':'hello world'}
    else:
        ack.user['ok'] = True
        return {'done': False, 'body':'hello world'}

try:
    httpd = TinyHttpdServer(19999)
    httpd.route('/', list_root)

    while True:
        done = httpd.step_forward(0.5)
        if done is True:
            break
except Exception, e:
    print e
finally:
    httpd.shut_down()
