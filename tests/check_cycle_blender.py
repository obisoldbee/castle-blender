import bpy,json,math
from mathutils import Vector
s=bpy.context.scene
o=next(o for o in s.objects if any(m.type=='OCEAN' for m in o.modifiers))
for m in o.modifiers:
 if m.type=='OCEAN':
  m.viewport_resolution=5
rows={}
verts={}
for f in [1,2,360,361,362,719,720,721]:
 s.frame_set(f)
 dg=bpy.context.evaluated_depsgraph_get(); e=o.evaluated_get(dg);mesh=e.to_mesh()
 verts[f]=[tuple(v.co) for v in mesh.vertices];e.to_mesh_clear()
 c=s.camera
 rows[f]={'camera':list(c.matrix_world.translation),'quat':list(c.matrix_world.to_quaternion()),'lens':c.data.lens,'moon':list(bpy.data.objects['MoonDisc'].location),'exposure':s.view_settings.exposure}
def rms(a,b):
 return math.sqrt(sum(sum((x-y)**2 for x,y in zip(v,w)) for v,w in zip(verts[a],verts[b]))/len(verts[a]))
r={f'{a}-{b}':rms(a,b) for a,b in [(1,721),(719,720),(720,1),(1,2),(360,361),(361,362)]}
assert r['1-721']<1e-6,r
assert 0 < r['720-1'] < 3*max(r['719-720'],r['1-2']),r
for k in ['camera','quat','lens','moon','exposure']:
 a,b=rows[1][k],rows[721][k]
 if not isinstance(a,list):a=[a];b=[b]
 assert max(abs(x-y) for x,y in zip(a,b))<1e-4,(k,a,b)
assert rows[719]['camera'] != rows[720]['camera']
print('PASS',json.dumps({'rows':rows,'ocean_rms':r,'vertices':len(verts[1])}))
