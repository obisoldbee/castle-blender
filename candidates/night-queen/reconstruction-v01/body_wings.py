import bpy,math
from mathutils import Vector,Quaternion
from math import sin,cos,pi

def mesh(name,verts,faces,mat):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);m.materials.append(mat)
 for p in m.polygons:p.use_smooth=True
 return o

def tube(name,pts,r,mat):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3;s=c.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
 for p,co in zip(s.bezier_points,pts):p.co=co;p.handle_left_type=p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(mat);return o

def rebuild_body_wings(stone):
 body=bpy.data.objects['GEO-body_female_realistic'];inv=body.matrix_world.inverted()
 for v in body.data.vertices:
  p=body.matrix_world@v.co;s=1 if p.x>=0 else -1
  if p.z<1.85:
   w=min(1,max(0,(1.85-p.z)/.55));w=w*w*(3-2*w)
   p.x-=s*.069*w*min(1,abs(p.x)/.075)
  # Roll palm toward observer about forearm; preserve wrist transition.
  if abs(p.x)>.55 and p.z>2.34:
   pivot=Vector((s*.65,-.05,2.39));axis=Vector((s*.48,0,.877)).normalized()
   w=min(1,max(0,(p.z-2.34)/.10));w=w*w*(3-2*w)
   p=pivot+Quaternion(axis,s*math.radians(88)*w)@(p-pivot)
   # Group the four fingers into the upright ancient palm silhouette.
   fw=min(1,max(0,(p.z-2.47)/.08))
   p.x=s*.735+(p.x-s*.735)*(1-.43*fw)
   # Relax the laterally extended thumb toward the transverse support.
   tw=math.exp(-((abs(p.x)-.61)/.055)**2-((p.z-2.43)/.035)**2)
   p.z+=.045*tw;p.x+=s*.025*tw
  v.co=inv@p
 for f in body.data.polygons:f.use_smooth=True
 for o in list(bpy.data.objects):
  if o.name.startswith(('Downswept primary feather','Wing overlapping coverts','Shoulder feather','Rod symbol','Ring symbol')):bpy.data.objects.remove(o,do_unlink=True)
 # Closed thickened silhouette, not a collection of pointed blades.
 for side in [-1,1]:
  outline=[(.25,2.47),(.34,2.44),(.42,2.25),(.52,2.04),(.68,1.72),(.73,1.51),(.66,1.48),(.49,1.54),(.32,1.66),(.26,1.94)]
  verts=[(side*x,y,z) for y in [.10,.19] for x,z in outline];n=len(outline)
  faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
  root=mesh('Rebuilt continuous wing root '+str(side),verts,faces,stone)
  bevel=root.modifiers.new('Soft sculpted wing edge','BEVEL');bevel.width=.035;bevel.segments=3
  # Rounded overlapping feathers embedded into wing body.
  for j in range(10):
   start=Vector((side*(.29+.019*j),.085,2.25-.024*j));end=Vector((side*(.35+.037*j),.075,1.62-.009*j))
   tangent=(end-start).normalized();cross=Vector((-tangent.z,0,tangent.x)).normalized();N=18;K=12;vs=[];fs=[]
   for i in range(N+1):
    t=i/N;center=start.lerp(end,t);w=.045*(sin(pi*t)**.32)+.003;depth=.017*sin(pi*t)+.002
    for k in range(K):
     a=2*pi*k/K;vs.append(tuple(center+cross*(w*cos(a))+Vector((0,depth*sin(a),0))))
   for i in range(N):
    for k in range(K):fs.append((i*K+k,i*K+(k+1)%K,(i+1)*K+(k+1)%K,(i+1)*K+k))
   fs.extend([tuple(range(K-1,-1,-1)),tuple(range(N*K,(N+1)*K))]);mesh('Rebuilt rounded primary '+str(side)+' '+str(j),vs,fs,stone)
  # Palm-forward symbolic ring and transverse rod, not vertical handles.
  cx=side*.735;cy=-.105;cz=2.56
  pts=[(cx+.105*cos(a),cy,cz+.105*sin(a))for a in [2*pi*i/32 for i in range(33)]]
  tube('Rebuilt hand ring '+str(side),pts,.011,stone)
  tube('Rebuilt transverse palm rod '+str(side),[(cx-.17,cy-.012,cz-.073),(cx,cy-.023,cz-.085),(cx+.17,cy-.012,cz-.073)],.012,stone)
