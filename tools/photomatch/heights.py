import os,sys,json,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from camlib import *
"""Heights from picked image rows above a known ground point.
input JSON: [{"id","cam","lon","lat","v":{"label":row,...}}]  (rows in full-image pixels)
The vertical through the ground point is projected; the height at which it reaches each picked row is reported,
plus the height implied if the picked base row (key 'base') is used as zero instead of the lidar ground."""
items=json.load(open(sys.argv[1])); out=[]
for it in items:
    K=json.load(open(it['cam'])); C=np.array(K['C']); a=(C,K['yaw'],K['pitch'],K['f'],K['cx'],K['cy'],K.get('roll',0))
    x,y=utm(it['lon'],it['lat']); g=z(x,y)
    hs=np.linspace(-5,25,3001); vs=np.array([project([x,y,g+h],*a)[0][1] for h in hs])
    def h_of(v): return float(np.interp(-v,-vs,hs))
    r={'id':it['id'],'cam':os.path.basename(it['cam']),'px_per_m':round(float(vs[1000]-vs[1100])/1.0,2)}
    b=h_of(it['v']['base']) if 'base' in it['v'] else 0.0
    for k,v in it['v'].items(): r[k]=round(h_of(v)-b,2)
    r['base_offset_m']=round(b,2); out.append(r); print(r)
if len(sys.argv)>2: json.dump(out,open(sys.argv[2],'w'),indent=1)
