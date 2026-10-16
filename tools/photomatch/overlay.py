import os
import sys,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from camlib import *
from PIL import Image,ImageDraw
img,camf,out=sys.argv[1],sys.argv[2],sys.argv[3]
K=json.load(open(camf)); C=np.array(K['C']); args=(C,K["yaw"],K["pitch"],K["f"],K["cx"],K["cy"],K.get("roll",0.0))
im=Image.open(img).convert('RGB'); d=ImageDraw.Draw(im)
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..')+'/'
def pt(lon,lat,h=0.5):
    x,y=utm(lon,lat); zz=z(x,y)
    if zz!=zz: return None
    q,dd=project([x,y,zz+h],*args); return (tuple(q) if dd>0 else None)
def line(coords,col,w=2):
    pts=[pt(*c) for c in coords]
    for a,b in zip(pts,pts[1:]):
        if a and b: d.line([a,b],fill=col,width=w)
O=json.load(open(R+'data/reference/osm_medora.geojson'))
for f in O['features']:
    k=f['properties']['kind'];g=f['geometry'];cs=g['coordinates'][0] if g['type']=='Polygon' else g['coordinates']
    col={'rail':(255,0,0),'road':(255,220,0),'water':(0,160,255),'building':(255,0,255)}[k]
    line(cs,col,3 if k=='rail' else 2)
H=json.load(open(R+'map/data/historic_features.geojson'))
for f in H['features']:
    g=f['geometry']
    if g['type']=='Point':
        q=pt(*g['coordinates'])
        if q: d.ellipse([q[0]-6,q[1]-6,q[0]+6,q[1]+6],outline=(0,255,0),width=3)
    elif g['type']=='Polygon': line(g['coordinates'][0],(0,255,0),2)
# DEM ridge/horizon: sample terrain along rays for skyline
W=im.width
for k,(uv) in K['gcp'].items():
    d.ellipse([uv[0]-8,uv[1]-8,uv[0]+8,uv[1]+8],outline=(0,255,255),width=3)
# skyline from DEM
sky=[]
for u in range(0,W,8):
    best=None
    Rm=rot(K["yaw"],K["pitch"],K.get("roll",0.0)); dv=Rm.T@np.array([(u-K['cx'])/K['f'],0,1.0]); az=math.atan2(dv[0],dv[1])
    maxang=-1
    for t in np.arange(50,9000,25):
        x,y=C[0]+math.sin(az)*t,C[1]+math.cos(az)*t
        try: h=z(x,y)
        except Exception: break
        if not (h==h and h>0): break
        a=(h-C[2])/t
        if a>maxang: maxang=a; best=(x,y,h)
    if best:
        q,dd=project(best,*args); sky.append(tuple(q))
for a,b in zip(sky,sky[1:]): d.line([a,b],fill=(255,128,0),width=3)
im.save(out)
