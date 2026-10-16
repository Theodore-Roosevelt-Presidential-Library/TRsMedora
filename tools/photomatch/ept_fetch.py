import json,sys,os,urllib.request,concurrent.futures as cf
from pyproj import Transformer
B='https://s3-us-west-2.amazonaws.com/usgs-lidar-public/ND_SouthWest_1_D21/'
OUT=sys.argv[1]; lon0,lat0,lon1,lat1=map(float,sys.argv[2:6])
T=Transformer.from_crs(4326,3857,always_xy=True)
x0,y0=T.transform(lon0,lat0); x1,y1=T.transform(lon1,lat1)
meta=json.load(urllib.request.urlopen(B+'ept.json'))
bx0,by0,bz0,bx1,by1,bz1=meta['bounds']
def get(u): return urllib.request.urlopen(u,timeout=60).read()
hier={}
def load_h(key):
    h=json.loads(get(B+'ept-hierarchy/'+key+'.json')); return h
def nb(d,x,y,z):
    s=(bx1-bx0)/2**d
    return bx0+x*s,by0+y*s,bx0+(x+1)*s,by0+(y+1)*s
todo=[]
def walk(h,key):
    d,x,y,z=map(int,key.split('-'))
    a,b,c,e=nb(d,x,y,z)
    if c<x0 or a>x1 or e<y0 or b>y1: return
    n=h.get(key)
    if n is None: return
    if n==-1:
        h2=load_h(key); walk(h2,key); return
    todo.append(key)
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                walk(h,f'{d+1}-{2*x+dx}-{2*y+dy}-{2*z+dz}')
walk(load_h('0-0-0-0'),'0-0-0-0')
print('nodes',len(todo)); os.makedirs(OUT,exist_ok=True)
def dl(k):
    f=f'{OUT}/{k}.laz'
    if not os.path.exists(f): open(f,'wb').write(get(B+'ept-data/'+k+'.laz'))
    return k
with cf.ThreadPoolExecutor(8) as ex: list(ex.map(dl,todo))
print('done')
