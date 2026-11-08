import bpy,math,os
from mathutils import Vector
from math import sin,cos,pi,exp
D=os.path.dirname(__file__);bpy.ops.wm.open_mainfile(filepath=D+'/Night_Queen_Claws_Crown.blend')
stone=bpy.data.materials['Warm carved limestone']
for o in list(bpy.data.objects):
 if o.name.startswith('Long avian toe'):bpy.data.objects.remove(o,do_unlink=True)
def bez(p,t):return p[0]*(1-t)**3+p[1]*3*t*(1-t)**2+p[2]*3*t*t*(1-t)+p[3]*t**3
def toe(name,points):
 p=list(map(Vector,points));vs=[];fs=[];N=192;K=48
 grooves=[.16+i*.043 for i in range(17)]
 for i in range(N+1):
  t=i/N;c=bez(p,t);d=(bez(p,min(1,t+.001))-bez(p,max(0,t-.001))).normalized();u=Vector((1,0,0));u=(u-d*u.dot(d)).normalized();v=d.cross(u).normalized()
  r=.028*(1-.46*t)+.009*exp(-((t-.27)/.065)**2)+.010*exp(-((t-.60)/.07)**2)+.007*exp(-((t-.84)/.055)**2)
  if t>.91:r*=1-.43*((t-.91)/.09)
  for k in range(K):
   a=2*pi*k/K;upper=max(0,sin(a))**.7
   # shallow irregular transverse incisions in the SAME closed toe surface
   ridge=sum(.0038*exp(-((t-g-.004*cos(a*2))/.007)**2) for g in grooves)
   rr=r-ridge*upper
   vs.append(tuple(c+u*cos(a)*rr+v*sin(a)*rr*.9))
 for i in range(N):
  for k in range(K):fs.append((i*K+k,i*K+(k+1)%K,(i+1)*K+(k+1)%K,(i+1)*K+k))
 fs.extend([tuple(range(K-1,-1,-1)),tuple(range(N*K,(N+1)*K))])
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(stone)
 for f in me.polygons:f.use_smooth=True
for s in [-1,1]:
 cx=s*.209
 for j in [-1,0,1]:
  ex=cx+j*.095;ey=-.235 if j==0 else -.195
  toe('Thick articulated toe with integral creases',[(cx+j*.023,.015,.415),(cx+j*.050,-.055,.402),(ex,ey+.045,.367),(ex,ey,.335)])
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=48;scene.render.resolution_x=1000;scene.render.resolution_y=800
bpy.ops.wm.save_as_mainfile(filepath=D+'/Night_Queen_Articulated_Toes.blend')
for n,loc,target,scale in [('toes_front',(0,-2,1.05),(0,-.07,.43),.85),('toes_oblique',(.65,-1.7,.97),(0,-.07,.43),.90),('toes_high',(.25,-.9,1.5),(0,-.07,.43),.90)]:
 cam.location=loc;cam.data.ortho_scale=scale;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=D+'/'+n+'.png';bpy.ops.render.render(write_still=True)
