import bpy,os,math
from mathutils import Vector
from math import exp,sin,cos,pi
D=os.path.dirname(__file__);bpy.ops.wm.open_mainfile(filepath=D+'/Night_Queen_Articulated_Toes.blend')
stone=bpy.data.materials['Warm carved limestone'];src=open(D+'/build.py').read();exec(src[src.index('def finish'):src.index('# body in')])
for o in list(bpy.data.objects):
 if o.name.startswith('Crown central'):bpy.data.objects.remove(o,do_unlink=True)
# keep compact layered horn crown; remove arbitrary central connector, reduce cone height
for o in list(bpy.data.objects):
 if o.name.startswith(('Continuous crown','Four pairs','Small crown top')):
  if o.type=='MESH':
   for v in o.data.vertices:
    w=o.matrix_world@v.co;w.z=2.99+(w.z-2.99)*.74;v.co=o.matrix_world.inverted()@w
  elif o.type=='CURVE':
   for s in o.data.splines:
    for p in s.bezier_points:
     w=o.matrix_world@p.co;w.z=2.99+(w.z-2.99)*.74;p.co=o.matrix_world.inverted()@w
# sculpt high resolution head by gentle continuous falloffs; no new disconnected face primitives
body=bpy.data.objects['GEO-body_female_realistic'];inv=body.matrix_world.inverted()
def g(x,z,cx,cz,sx,sz):return exp(-((x-cx)/sx)**2-((z-cz)/sz)**2)
for v in body.data.vertices:
 p=body.matrix_world@v.co;x,y,z=p
 if z<2.62 or y>-.10:continue
 mask=min(1,max(0,(-y-.10)/.06))
 cheek=g(abs(x),z,.085,2.82,.065,.10)
 p.x+=x*.17*cheek*mask # fuller cheek and gentler oval outline
 p.y-=.009*cheek*mask
 p.z+=.012*g(x,z,0,2.675,.105,.045)*mask # shorter, rounded lower chin
 p.y+=.014*g(x,z,0,2.865,.035,.065)*mask # gentler nasal projection
 p.y+=.005*g(x,z,0,2.945,.10,.035)*mask # soften heavy brow
 p.z+=.008*g(abs(x),z,.043,2.765,.023,.027)*mask # quietly lifted lip corners
 p.x+=x*.06*g(abs(x),z,.062,2.912,.040,.025)*mask
 v.co=inv@p
# calm carved eyes rather than deep vacant apertures; solid stone surfaces sit behind existing lids
for s in [-1,1]:
 uv('Quiet carved eye', (s*.056,-.216,2.917),(.025,.010,.010))
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=48;scene.render.resolution_x=900;scene.render.resolution_y=1000
bpy.ops.wm.save_as_mainfile(filepath=D+'/Night_Queen_Serene_Study.blend')
for n,loc,target,scale in [('serene_face_front',(0,-5,3.03),(0,-.03,2.97),.85),('serene_face_oblique',(1.5,-4,3.15),(0,-.03,2.97),.9),('serene_full',(3,-7,3.1),(0,0,1.72),3.75)]:
 cam.location=loc;cam.data.ortho_scale=scale;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=D+'/'+n+'.png';bpy.ops.render.render(write_still=True)
