import os
import sys,json,numpy as np
from PIL import Image,ImageDraw,ImageFilter
img,x0,x1,y0,y1,out=sys.argv[1],*map(int,sys.argv[2:6]),sys.argv[6]
im=Image.open(img).convert('L').filter(ImageFilter.GaussianBlur(3)); A=np.asarray(im,float)
pts=[]
for x in range(x0,x1,15):
    col=A[y0:y1,x-3:x+4].mean(axis=1)
    g=col[:-12]-col[12:]   # bright above, dark below
    i=int(np.argmax(g)); pts.append((x,y0+i+6,float(g[i])))
json.dump(pts,open(out,'w'))
d=ImageDraw.Draw(c:=Image.open(img).convert('RGB'))
for x,y,g in pts: d.ellipse([x-4,y-4,x+4,y+4],outline=(255,0,0),width=2)
c.thumbnail((1500,1500)); c.save(out.replace('.json','.jpg'))
