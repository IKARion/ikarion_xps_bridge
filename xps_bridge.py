#!/bin/sh
'''which' python3 > /dev/null && exec python3 "$0" "$@" || exec python "$0" "$@"
'''


#
#  2018, m6c7l
#
 
from flask import Flask, request, g
from flask_httpauth import HTTPTokenAuth

import xmlrpc.client

import json, time, sys, os

# ========================================================================

millis = lambda: int(round(time.time() * 1000))

# ------------------------------------------------------------------------

file_name =  os.path.basename(sys.argv[0])
script_name = os.path.splitext(file_name)[0]

token_access = json.load(open(script_name + '.json'))

# ------------------------------------------------------------------------

def lookup_token(token):
    if token in token_access:
        return token_access[token]
    return None

# ------------------------------------------------------------------------

def process_request(client, request, backup=False):

    origin = None

    if request.remote_addr in client:
        origin = client[request.remote_addr]
    elif 'any' in client:
        origin = client['any']

    if origin is None:
        return None, None, None

    size, dump, data, log = 0, None, None, None

    try:
        dump = json.dumps(request.get_json(), ensure_ascii=False)  # non-printable chars
        size = +1
    except Exception as e:
        dump = request.data.decode('utf-8')
        size = -1
        log = str(e)

    size = size * len(dump)

    d = {}
    d['date'] = time.strftime('%Y-%m-%d')
    d['time'] = time.strftime('%H:%M:%S')
    d['address'] = request.remote_addr
    d['client'] = origin
    d['size'] = abs(size)
    d['error'] = log
    d['content'] = ''

    # print(request.data.decode('unicode_escape'))

    if size > 0:
        data = json.loads(dump)
        if not backup:
            print(mapify(d, request.data.decode('utf-8')), file=sys.stdout, flush=True)
    else:
        data = None
        if not backup:
            print(mapify(d, request.data.decode('utf-8')), file=sys.stderr, flush=True)

    return abs(size), data, dump

# ------------------------------------------------------------------------

def mapify(d, content):
    s = str(d)
    rep = (('{', ''), ('}',''), ("''", '{}'), ("'", ""), (': ', '='))
    for r in rep: s = s.replace(r[0], r[1])
    s = s.format(content)
    return s

# ========================================================================

proxy = xmlrpc.client.ServerProxy("http://0.0.0.0:50100/", allow_none=True)

# ------------------------------------------------------------------------

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Token')

# ------------------------------------------------------------------------

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

# ------------------------------------------------------------------------

@auth.verify_token
def verify_token(token):
    g.token = lookup_token(token)
    return g.token is not None

# ------------------------------------------------------------------------

@app.route('/', methods=['POST'])
@auth.login_required
def index():

    client = g.token

    is_local = '127.0.0.1' in client
        
    size, result, js = process_request(client, request, silent and is_local)

    value = None

    if result is not None:  # insert data via RPC
                
        if not silent or is_local:
            try:
                #value = proxy.xps.add(result)  # type(result) is dict, becomes Map in Java
                value = proxy.xps.add(js)  # simple JSON string, becomes Tuple in Java                
            except Exception as e:
                print('RPC client - - {}'.format(e), file=sys.stderr)
                sys.stderr.flush()
        else:
            return '', 202, {'Content-Type': 'text/plain'}

        if value is None:
            return '{{"size": {}, "accept": {}}}'.format(size, +1).lower(), 200, {'Content-Type': 'application/json'}
        else:
            if len(value) == 0:
                return '{{"size": {}, "accept": {}}}'.format(size, 0).lower(), 200, {'Content-Type': 'application/json'}
            else:
                return value, 200, {'Content-Type': 'application/json'}
    
    else:
        if size is not None:
            return '{{"size": {}, "accept": {}}}'.format(size, -1).lower(), 200, {'Content-Type': 'application/json'}
        else:
            return '', 401, {'Content-Type': 'text/plain'}

        
# ========================================================================

if __name__ == '__main__':
    
    silent = False
    
    try:
        
        if sys.argv[-1] == 'silent': silent = True
        
        try:  # production
            from gevent.pywsgi import WSGIServer
            http_server = WSGIServer(('0.0.0.0', 50101), app)
            print('[ OK ] XPS WSGI bridge', file=sys.stderr)
            http_server.serve_forever()
            
        except ImportError:  # development
            app.run(host='0.0.0.0', port=50101)            
            print('[ OK ] XPS bridge', file=sys.stderr)

    except Exception as e:
        print('[fail] XPS bridge - - {}'.format(e), file=sys.stderr)

