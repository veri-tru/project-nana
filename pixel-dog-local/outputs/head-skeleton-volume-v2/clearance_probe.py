"""Implementation preflight: new jaw surface against new upper field, not final review."""
import json,sys
import numpy as np
import build as m
profiles=json.loads((m.HERE/'profiles.json').read_text('utf-8'))
for breed in (sys.argv[1:] or m.BREEDS):
    ff,a=m.fields(profiles[breed]);d=a['d'];W=a['W'];h=a['hinge']
    v,f,n=m.extract(ff['jaw'],[(d[5,0]-3,8),(-10,d[0,1]+5),(-W*1.55,W*1.55)],.8)
    samples=np.concatenate([v,v[f].mean(1)])
    allowed=np.min(np.linalg.norm(samples[:,None]-np.array([h+[0,0,s*W*.8] for s in [-1,1]])[None],axis=-1),axis=1)>3.5
    values=[]
    for angle in range(0,21,2):
        posed=m.rotate(samples,h,angle);dist=ff['upper'](posed);i=np.flatnonzero(allowed)[np.argmin(dist[allowed])]
        values.append({'angle':angle,'min':float(dist[i]),'point':posed[i].tolist()})
    print(breed,json.dumps(values),flush=True)
