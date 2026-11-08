import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from body_wings import rebuild_body_wings
from face import rebuild_face
from crown import rebuild_crown
from claws import rebuild_claws
bpy.ops.wm.open_mainfile(filepath=str(D.parent/'remediation/Night_Queen_Cleanup_Study.blend'))
mat=bpy.data.materials.new('Neutral reconstruction clay');mat.diffuse_color=(.48,.46,.43,1)
rebuild_body_wings(mat);rebuild_face(mat);rebuild_crown(mat)
feet=rebuild_claws(mat)
for foot in feet:
 low=min((foot.matrix_world@v.co).z for v in foot.data.vertices)
 foot.location.z += .3102-low
for o in bpy.context.scene.objects:
 if o.type in ['MESH','CURVE'] and 'Studio' not in o.name:o.data.materials.clear();o.data.materials.append(mat)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=False;s.cycles.max_bounces=4;s.render.resolution_percentage=100
views=[('Full front',(0,-7,2),(0,0,1.75),3.55,750,1000),('Head front',(0,-5,3),(0,0,2.96),.80,800,900),('Full oblique',(3,-7,2.8),(0,0,1.75),3.55,750,1000),('Feet oblique',(.65,-1.6,.9),(0,-.07,.43),.72,900,650)]
cams=[]
for name,loc,target,scale,w,h in views:
 data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale;c=bpy.data.objects.new(name,data);s.collection.objects.link(c);c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();cams.append(c)
s.camera=cams[0];s.render.resolution_x=750;s.render.resolution_y=1000;s.render.filepath='//renders/full_front.png'
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Night_Queen_Reconstruction_v01.blend'))
records=[]
for c,(name,loc,target,scale,w,h) in zip(cams,views):
 s.camera=c;s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(D/(name.lower().replace(' ','_')+'.png'));bpy.ops.render.render(write_still=True);records.append({'view':name,'file':s.render.filepath,'camera_location':loc,'target':target,'ortho_scale':scale,'samples':48})
(D/'render_manifest.json').write_text(json.dumps({'model_sha256':hashlib.sha256((D/'Night_Queen_Reconstruction_v01.blend').read_bytes()).hexdigest(),'views':records,'status':'unapproved reconstruction study, not production','formal_scene_changed':False},indent=2))
