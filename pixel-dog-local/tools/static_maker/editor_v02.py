"""Loopback-only authoring editor; preview, save, compare and restore draft states."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import urlparse

import maker
from render_v02 import preview, png_data
from state_v02 import StateStore, GEOMETRY, COAT_PARTS

ROOT=Path(__file__).resolve().parent

def make_server(db,dog,port=8765):
    token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send_json(self,payload,status=200):
            data=json.dumps(payload,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
        def same_origin(self):
            expected=f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host')!=expected:return False
            origin=self.headers.get('Origin')
            return origin is None or origin==f'http://{expected}'
        def do_GET(self):
            if not self.same_origin():return self.send_json({'error':'local origin required'},403)
            path=urlparse(self.path).path
            if path=='/':
                data=(ROOT/'editor.html').read_text().replace('__SESSION_TOKEN__',token).encode()
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data);return
            if path!='/api/state':return self.send_json({'error':'not found'},404)
            store=StateStore(db)
            try:
                state,rev=store.state_get(dog);p,_=store.get(dog,state['source_profile']['revision'])
                before={f'{v}-{s}':png_data(maker.build(p,s,v)[0]) for v in ('face','full') for s in ('B2','C2')}
                self.send_json({'state':state,'revision':rev,'history':store.state_history(dog),
                                'ranges':GEOMETRY,'coat_parts':COAT_PARTS,'preview':preview(state),'legacy':before})
            except ValueError as e:self.send_json({'error':str(e)},400)
            finally:store.close()
        def do_POST(self):
            if not self.same_origin() or self.headers.get('X-Nana-Session')!=token:
                return self.send_json({'error':'invalid local session'},403)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=100000:raise ValueError('invalid body size')
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict):raise ValueError('object required')
            except (ValueError,TypeError) as e:return self.send_json({'error':str(e)},400)
            path=urlparse(self.path).path
            if path not in ('/api/preview','/api/save','/api/restore'):return self.send_json({'error':'not found'},404)
            store=StateStore(db)
            try:
                if path=='/api/restore':
                    rev=store.state_restore(dog,data['target'],data['expected'])
                    state,_=store.state_get(dog,rev)
                else:
                    state=data['state']
                    if not isinstance(state,dict) or state.get('dog_id')!=dog:raise ValueError('dog mismatch')
                    p,_=store.get(dog,state['source_profile']['revision'])
                    if maker.digest(maker.canonical(p).encode())!=state['source_profile']['sha256']:raise ValueError('profile mismatch')
                    if path=='/api/preview':return self.send_json({'preview':preview(state)})
                    rev=store.state_save(state,data['expected'],data['reason'])
                self.send_json({'state':state,'revision':rev,'history':store.state_history(dog),'preview':preview(state)})
            except (ValueError,KeyError,TypeError) as e:
                status=409 if 'stale' in str(e) else 400
                self.send_json({'error':str(e)},status)
            finally:store.close()
    return HTTPServer(('127.0.0.1',port),Handler)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--db',required=True);ap.add_argument('--dog',required=True);ap.add_argument('--port',type=int,default=8765)
    args=ap.parse_args();store=StateStore(args.db)
    try:store.state_get(args.dog)
    finally:store.close()
    server=make_server(args.db,args.dog,args.port)
    print(f'http://127.0.0.1:{server.server_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
