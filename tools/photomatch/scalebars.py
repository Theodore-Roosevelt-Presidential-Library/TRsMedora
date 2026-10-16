import os,sys,json,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from camlib import *
from PIL import Image,ImageDraw
"""Draw vertical height scales (ticks every metre, labelled every 3 m) standing on the ground at given points.
usage: scalebars.py cam.json photo.jpg points.json out.png x0 y0 x1 y1 scale
points.json: [{"id":..,"lon":..,"lat":..}]"""
K=json.load(open(sys.argv[1])); C=np.array(K['C']); a=(C,K['yaw'],K['pitch'],K['f'],K['cx'],K['cy'],K.get('roll',0))
im=Image.open(sys.argv[2]).convert('RGB'); d=ImageDraw.Draw(im)
pts=json.load(open(sys.argv[3])); out={}
for p in pts:
    x,y=utm(p['lon'],p['lat']); g=z(x,y); prev=None; ticks=[]
    for h in range(0,31):
        q,_=project([x,y,g+h],*a); ticks.append(q)
        if prev is not None: d.line([tuple(prev),tuple(q)],fill=(255,0,0),width=2)
        w=6 if h%3==0 else 3
        d.line([(q[0]-w,q[1]),(q[0]+w,q[1])],fill=(255,255,0) if h%3==0 else (255,0,0),width=1)
        if h%3==0: d.text((q[0]+7,q[1]-6),str(h),fill=(255,255,0))
        prev=q
    d.text((ticks[0][0]-10,ticks[0][1]+4),p['id'],fill=(0,255,255))
    out[p['id']]={'v_per_m':float(ticks[0][1]-ticks[1][1]),'base':[float(ticks[0][0]),float(ticks[0][1])],'top15':[float(ticks[30][0]),float(ticks[15][1])]}
x0,y0,x1,y1=map(int,sys.argv[5:9]); sc=float(sys.argv[9])
im=im.crop((x0,y0,x1,y1)); im=im.resize((int((x1-x0)*sc),int((y1-y0)*sc)),Image.LANCZOS); im.save(sys.argv[4])
print(json.dumps(out))
