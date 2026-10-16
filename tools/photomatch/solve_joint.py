import os
import sys,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from camlib import *
from scipy.optimize import least_squares
cfg=json.load(open(sys.argv[1]))
G=cfg['gcp']; H=[tuple(p[:2]) for p in json.load(open(cfg['horizon']))]
excl=cfg.get('horizon_exclude',[])
H=[p for p in H if not any(a<=p[0]<=b for a,b in excl)]
ys=np.array([p[1] for p in H]); med=np.array([np.median(ys[max(0,i-3):i+4]) for i in range(len(ys))])
H=[p for p,m in zip(H,med) if abs(p[1]-m)<12]
P={k:np.array([*utm(*v['lonlat']),0.0]) for k,v in G.items()}
for k,v in G.items(): P[k][2]=z(P[k][0],P[k][1])+v.get('h',2.0)
CX,CY=cfg['cx'],cfg['cy']; wh=cfg.get('w_horizon',0.5)
def resid(p):
    X,Y,dz,yaw,pitch,roll,f=p
    C=np.array([X,Y,z(X,Y)+dz]); r=[]
    for k,v in G.items():
        q,d=project(P[k],C,yaw,pitch,f,CX,CY,roll)
        r+=list((q-np.array(v['uv']))*v.get('w',1)) if d>0 else [1e4,1e4]
    for u,vv in H:
        d=ray_dir(u,vv,yaw,pitch,f,CX,CY,roll); az=math.atan2(d[0],d[1]); el=math.atan2(d[2],math.hypot(d[0],d[1]))
        r.append(wh*f*(el-sky_elev(C,az)))
    return np.array(r)
x0=cfg['init']
s=least_squares(resid,x0,x_scale=[20,20,2,1,0.5,0.5,100],bounds=([x0[0]-600,x0[1]-600,0.5,x0[3]-30,-30,-5,800],[x0[0]+600,x0[1]+600,40,x0[3]+30,10,5,9000]))
X,Y,dz,yaw,pitch,roll,f=s.x; C=np.array([X,Y,z(X,Y)+dz])
r=s.fun; ng=2*len(G)
print('cam',ll(X,Y),'ground',round(z(X,Y),1),'dz',round(dz,1),'yaw',round(yaw,2),'pitch',round(pitch,2),'roll',round(roll,2),'f',round(f))
print('gcp resid px',r[:ng].reshape(-1,2).round(1).tolist())
print('horizon rms px',round(float(np.sqrt(np.mean((r[ng:]/wh)**2))),1),'n',len(H))
json.dump({'C':C.tolist(),'yaw':yaw,'pitch':pitch,'roll':roll,'f':f,'cx':CX,'cy':CY,'gcp':{k:v['uv'] for k,v in G.items()}},open(cfg['out'],'w'))
