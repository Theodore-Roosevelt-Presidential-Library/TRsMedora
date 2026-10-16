import json, numpy as np, math
from pyproj import Transformer
import os
S=os.environ.get('PHOTOMATCH_WORK','work').rstrip('/')+'/'
DEM=np.load(S+'dem/dem5.npy'); M=json.load(open(S+'dem/dem5.json'))
X0,Y1,RES=M['x0'],M['y1'],M['res']
T=Transformer.from_crs(4326,26913,always_xy=True); Ti=Transformer.from_crs(26913,4326,always_xy=True)
def utm(lon,lat): return T.transform(lon,lat)
def ll(x,y): return Ti.transform(x,y)
def z(x,y):
    c=(x-X0)/RES-0.5; r=(Y1-y)/RES-0.5
    c0,r0=int(math.floor(c)),int(math.floor(r)); fc,fr=c-c0,r-r0
    if r0<0 or c0<0 or r0+2>DEM.shape[0] or c0+2>DEM.shape[1]: return float('nan')
    a=DEM[r0:r0+2,c0:c0+2]
    return float(a[0,0]*(1-fc)*(1-fr)+a[0,1]*fc*(1-fr)+a[1,0]*(1-fc)*fr+a[1,1]*fc*fr)
def rot(yaw,pitch,roll=0.0):
    # camera looks along yaw (deg clockwise from north), pitch (deg, negative=down); returns rows: right, up, forward in ENU
    y,p,r=map(math.radians,(yaw,pitch,roll))
    f=np.array([math.sin(y)*math.cos(p), math.cos(y)*math.cos(p), math.sin(p)])
    rt=np.array([math.cos(y), -math.sin(y), 0.0])
    up=np.cross(rt,f)
    if r: 
        c,s=math.cos(r),math.sin(r); rt,up=c*rt+s*up, -s*rt+c*up
    return np.vstack([rt,up,f])
def project(P,C,yaw,pitch,f,cx,cy,roll=0.0):
    R=rot(yaw,pitch,roll); v=R@(np.asarray(P,float)-np.asarray(C,float))
    return np.array([cx+f*v[0]/v[2], cy-f*v[1]/v[2]]), v[2]
def ray_ground(u,v,C,yaw,pitch,f,cx,cy,roll=0.0,maxd=4000,step=2.0):
    R=rot(yaw,pitch,roll); d=R.T@np.array([(u-cx)/f, -(v-cy)/f, 1.0]); d/=np.linalg.norm(d)
    t=step; prev=None
    while t<maxd:
        p=np.asarray(C)+d*t
        h=p[2]-z(p[0],p[1])
        if h<0:
            # refine
            lo,hi=t-step,t
            for _ in range(20):
                m=(lo+hi)/2; q=np.asarray(C)+d*m
                if q[2]-z(q[0],q[1])<0: hi=m
                else: lo=m
            return np.asarray(C)+d*hi, hi
        t+=step
    return None,None

def zv(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float)
    c=(x-X0)/RES-0.5; r=(Y1-y)/RES-0.5
    c0=np.floor(c).astype(int); r0=np.floor(r).astype(int); fc=c-c0; fr=r-r0
    ok=(c0>=0)&(r0>=0)&(c0+1<DEM.shape[1])&(r0+1<DEM.shape[0])
    c0=np.clip(c0,0,DEM.shape[1]-2); r0=np.clip(r0,0,DEM.shape[0]-2)
    v=DEM[r0,c0]*(1-fc)*(1-fr)+DEM[r0,c0+1]*fc*(1-fr)+DEM[r0+1,c0]*(1-fc)*fr+DEM[r0+1,c0+1]*fc*fr
    return np.where(ok,v,np.nan)
TS=np.concatenate([np.arange(30,1000,10),np.arange(1000,14000,30)])
def sky_elev(C,az):
    x=C[0]+np.sin(az)*TS; y=C[1]+np.cos(az)*TS
    h=zv(x,y)-TS**2/(2*6.371e6)*0.87
    a=np.arctan2(h-C[2],TS)
    return np.nanmax(a)
def ray_dir(u,v,yaw,pitch,f,cx,cy,roll=0.0):
    R=rot(yaw,pitch,roll); d=R.T@np.array([(u-cx)/f,-(v-cy)/f,1.0]); return d/np.linalg.norm(d)
