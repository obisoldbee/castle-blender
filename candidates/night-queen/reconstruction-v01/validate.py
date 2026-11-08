import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
D=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(D/'Night_Queen_Reconstruction_v01.blend'))
def bounds(o):
 deps=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(deps)
 pts=[e.matrix_world@Vector(c)for c in e.bound_box]
 return [[min(p[i]for p in pts),max(p[i]for p in pts)]for i in range(3)]
feet=[o for o in bpy.data.objects if o.get('contact_plane_z') is not None]
r={'objects':len(bpy.data.objects),'old_eyes_remaining':[o.name for o in bpy.data.objects if o.name.startswith('GEO-body_female_realistic.eye')],'cameras':[o.name for o in bpy.data.objects if o.type=='CAMERA'],'feet':{o.name:bounds(o)for o in feet},'embedded_scripts':len(bpy.data.texts),'linked_libraries':len(bpy.data.libraries),'candidate_status':'not accepted; head/neck seams, hand posture, horn cap and joint shaping remain'}
assert not r['old_eyes_remaining'];assert len(feet)==2
assert all(abs(bounds(o)[2][0]-.3102)<.0001 for o in feet)
(D/'verification.json').write_text(json.dumps(r,indent=2));print('CANDIDATE_CHECK',json.dumps(r))
