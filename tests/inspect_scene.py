"""Read-only acceptance inspection; run with Blender --disable-autoexec FILE --python THIS."""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
out=Path(args[0]); s=bpy.context.scene
report={'blender':bpy.app.version_string,'objects':len(s.objects),'active_camera':s.camera.name if s.camera else None,'output':s.render.filepath,'samples':s.cycles.samples,'texts':len(bpy.data.texts),'drivers':sum(len(x.animation_data.drivers) for x in list(bpy.data.objects)+list(bpy.data.materials)+list(bpy.data.worlds) if x.animation_data),'external_libraries':len(bpy.data.libraries),'collections':[c.name for c in bpy.data.collections], 'provenance':dict(s.items())}
report['gargoyles']={o.name:dict(o.items()) for o in s.objects if 'garg' in o.name.lower()}
report['finials']=[]
# Match small sphere geometry to nearby vertical thin cone geometry, by original bounds.
cones=[]; balls=[]
for o in s.objects:
 if o.type!='MESH': continue
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 if not pts: continue
 lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
 d=hi-lo
 if o.get('castle_asset')=='pinnacle_tip' or (o.name.startswith('Cone') and .2<d.x<.4 and .9<d.z<1.3): cones.append((o,lo,hi))
 if o.get('castle_asset')=='pinnacle_ball' or (o.name.startswith('Sphere') and .1<d.x<.15 and .1<d.z<.15): balls.append((o,lo,hi))
dg=bpy.context.evaluated_depsgraph_get()
for ball,bl,bh in balls:
 for cone,cl,ch in cones:
  if abs((bl.x+bh.x-cl.x-ch.x)/2)<.02 and abs((bl.y+bh.y-cl.y-ch.y)/2)<.02 and abs(bl.z-ch.z)<.1:
   co=cone.evaluated_get(dg);bo=ball.evaluated_get(dg)
   top=max((co.matrix_world@v.co).z for v in co.data.vertices);bottom=min((bo.matrix_world@v.co).z for v in bo.data.vertices)
   report['finials'].append({'ball':ball.name,'cone':cone.name,'gap':bottom-top})
if s.frame_end==720 and s.camera:
 frames={}
 for f in (1,2,719,720,721):
  s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();cam=s.camera.evaluated_get(dg)
  moon=bpy.data.objects.get('MoonDisc')
  frames[str(f)]={'camera':list(cam.matrix_world.translation),'camera_rotation':list(cam.matrix_world.to_quaternion()),'lens':s.camera.data.lens,'moon':list(moon.location) if moon else None,'exposure':s.view_settings.exposure}
 report['frames']=frames
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,default=str));print('ACCEPTANCE',out)
