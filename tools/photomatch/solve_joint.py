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
H=H[::cfg.get('h_every',1)]
P={k:np.array([*utm(*v['lonlat']),0.0]) for k,v in G.items()}
for k,v in G.items(): P[k][2]=z(P[k][0],P[k][1])+v.get('h',2.0)
LINES=[]
for L in cfg.get('lines',[]):
    P2=[]
    for lon,lat in L['lonlat']:
        x,y=utm(lon,lat); P2.append(np.array([x,y,z(x,y)+L.get('h',0)]))
    LINES.append({'P':P2,'uv':L['uv'],'w':L.get('w',1)})
CX,CY=cfg['cx'],cfg['cy']; wh=cfg.get('w_horizon',0.5)
def resid(p):
    X,Y,dz,yaw,pitch,roll,f=p
    C=np.array([X,Y,z(X,Y)+dz]); r=[]
    for k,v in G.items():
        q,d=project(P[k],C,yaw,pitch,f,CX,CY,roll)
        w=v.get('w',1); r+=[(q[0]-v['uv'][0])*w*v.get('wu',1),(q[1]-v['uv'][1])*w*v.get('wv',1)] if d>0 else [1e4,1e4]
    for L in LINES:
        (a,_),(b,_)=[project(q,C,yaw,pitch,f,CX,CY,roll) for q in L['P']]
        n=np.array([-(b-a)[1],(b-a)[0]]); n/=np.linalg.norm(n)
        for uv in L['uv']: r.append(L.get('w',1)*float(np.dot(np.array(uv)-a,n)))
    for u,vv in H:
        d=ray_dir(u,vv,yaw,pitch,f,CX,CY,roll); az=math.atan2(d[0],d[1]); el=math.atan2(d[2],math.hypot(d[0],d[1]))
        r.append(wh*f*(el-sky_elev(C,az)))
    return np.array(r)
DZMAX=cfg.get('dz_max',60); FMIN=cfg.get('f_min',300); FMAX=cfg.get('f_max',9000)
def fit(x0,R=600):
    x0=list(x0); x0[2]=min(x0[2],DZMAX-0.1); x0[6]=min(max(x0[6],FMIN+1),FMAX-1)
    return least_squares(resid,x0,x_scale=[20,20,2,1,0.5,0.5,100],bounds=([x0[0]-R,x0[1]-R,0.5,x0[3]-40,-30,-5,FMIN],[x0[0]+R,x0[1]+R,DZMAX,x0[3]+40,10,5,FMAX]))
if 'grid' in cfg:
    # multi-start: aim each start at a target point so yaw starts sensibly
    g=cfg['grid']; best=None
    tx,ty=utm(*g['target'])
    for gx in np.arange(g['x0'],g['x1']+1,g['step']):
        for gy in np.arange(g['y0'],g['y1']+1,g['step']):
            if not np.isfinite(z(gx,gy)) or z(gx,gy)<g.get('zmin',-1e9): continue
            for dyaw in g.get('yaw_offsets',[0]):
                yaw0=math.degrees(math.atan2(tx-gx,ty-gy))+dyaw
                try: s=fit([gx,gy,g.get('dz',2),yaw0,g.get('pitch',-3),0,g.get('f',2500)],R=g['step'])
                except Exception as e: continue
                if best is None or s.cost<best.cost: best=s
    s=best
else:
    s=fit(cfg['init'],R=cfg.get('R',600))
X,Y,dz,yaw,pitch,roll,f=s.x; C=np.array([X,Y,z(X,Y)+dz])
r=s.fun; ng=2*len(G)
print('cam',ll(X,Y),'ground',round(z(X,Y),1),'dz',round(dz,1),'yaw',round(yaw,2),'pitch',round(pitch,2),'roll',round(roll,2),'f',round(f))
print('gcp resid px',r[:ng].reshape(-1,2).round(1).tolist())
print('horizon rms px',round(float(np.sqrt(np.mean((r[ng:]/wh)**2))),1),'n',len(H))
json.dump({'C':C.tolist(),'yaw':yaw,'pitch':pitch,'roll':roll,'f':f,'cx':CX,'cy':CY,'gcp':{k:v['uv'] for k,v in G.items()}},open(cfg['out'],'w'))
