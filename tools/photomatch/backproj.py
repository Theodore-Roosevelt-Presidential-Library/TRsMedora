import os
import sys,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from camlib import *
from shapely.geometry import shape,Point
K=json.load(open(sys.argv[1])); pts=json.load(open(sys.argv[2]))
C=np.array(K['C'])
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..')+'/'
PAR=json.load(open(R+'data/reference/parcels_medora_ndgishub.geojson'))
OSM=json.load(open(R+'data/reference/osm_medora.geojson'))
H=json.load(open(R+'map/data/historic_features.geojson'))
out=[]
for name,(u,v) in pts.items():
    p,dist=ray_ground(u,v,C,K['yaw'],K['pitch'],K['f'],K['cx'],K['cy'],K.get('roll',0.0),step=1.0)
    if p is None: print(name,'no hit'); continue
    lon,lat=ll(p[0],p[1]); P=Point(lon,lat)
    # sensitivity: 3 px vertical error -> ground shift
    p2,_=ray_ground(u,v+3,C,K['yaw'],K['pitch'],K['f'],K['cx'],K['cy'],K.get('roll',0.0),step=1.0)
    err=float(np.hypot(*(p2[:2]-p[:2]))) if p2 is not None else None
    blk=[f['properties']['Block'] for f in PAR['features'] if shape(f['geometry']).contains(P)]
    nh=min(H['features'],key=lambda f:shape(f['geometry']).distance(P))
    dnh=shape(nh['geometry']).distance(P)*111000
    no=min([f for f in OSM['features'] if f['properties']['kind']=='building'],key=lambda f:shape(f['geometry']).distance(P))
    out.append({'id':name,'uv':[u,v],'lon':round(lon,6),'lat':round(lat,6),'dist_m':round(dist),'m_per_3px':round(err,1) if err else None,'block':blk,'nearest_hist':nh['properties']['id'],'d_hist_m':round(dnh),'nearest_osm':no['properties']['name'] or no['properties']['osm'],'d_osm_m':round(shape(no['geometry']).distance(P)*111000)})
    print(out[-1])
json.dump(out,open(sys.argv[3],'w'),indent=1)
