"""Local editor for mixed v2/v3 history, with explicit upgrade and reversible state."""
import argparse
import sys

import maker
import render_v02
import render_v03
import state_v02
from state_v03 import StateStore, GEOMETRY, COAT_PARTS, migrate
from editor_v02 import make_server as shared_server

def preview(state):
    return (render_v02 if state.get('schema_version')==2 else render_v03).preview(state)

def context(store,state):
    if state['schema_version']==3:
        old,_=store.state_get(state['dog_id'],state['migration']['from_authoring_revision'])
        images={f'{v}-{s}':render_v02.png_data(render_v02.build(old,s,v)[0]) for v in ('face','full') for s in ('B2','C2')}
        return {'ranges':GEOMETRY,'coat_parts':COAT_PARTS,'legacy':images,
                'render_label':'0.3','comparison_label':'0.2','can_migrate':False}
    p,_=store.get(state['dog_id'],state['source_profile']['revision'])
    images={f'{v}-{s}':render_v02.png_data(maker.build(p,s,v)[0]) for v in ('face','full') for s in ('B2','C2')}
    return {'ranges':state_v02.GEOMETRY,'coat_parts':COAT_PARTS,'legacy':images,
            'render_label':'0.2','comparison_label':'0.1','can_migrate':True}

def upgrade(store,dog,expected):
    state,revision=store.state_get(dog)
    if revision!=expected:raise ValueError('stale authoring revision')
    return store.state_save(migrate(state,revision),expected,'explicit v0.2 to v0.3 migration')

def make_server(db,dog,port=8765):
    return shared_server(db,dog,port,engine=sys.modules[__name__])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',required=True);parser.add_argument('--dog',required=True)
    parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    store=StateStore(args.db)
    try:store.state_get(args.dog)
    finally:store.close()
    server=make_server(args.db,args.dog,args.port)
    print(f'http://127.0.0.1:{server.server_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
