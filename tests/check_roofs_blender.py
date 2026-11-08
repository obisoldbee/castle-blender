"""Read-only roof proportions and dormer cone intersection acceptance."""
import bpy,json,sys,math
from pathlib import Path
s=bpy.context.scene;rows=[];dormers=[]
def pts(o):return [o.matrix_world@v.co for v in o.data.vertices]
roofs={o.name:o for o in s.objects if o.get('castle_asset')=='tower_roof'}
assert len(roofs)==15,len(roofs)
for name,o in roofs.items():
 p=pts(o);lo=min(v.z for v in p);hi=max(v.z for v in p);radius=o['roof_radius'];height=hi-lo
 assert abs(height-o['roof_original_height']*.65)<1e-4,(name,height)
 assert abs((max(v.x for v in p)-min(v.x for v in p))/2-radius)<1e-4,name
 related=[q for q in s.objects if q.get('roof_owner')==name]
 fin=[q for q in related if q.get('castle_asset')=='roof_finial'];balls=[q for q in related if q.get('castle_asset')=='roof_finial_ball']
 assert len(fin)==len(balls)==1,name
 assert abs(min(v.z for v in pts(fin[0]))-(hi-.1))<1e-4,name
 assert abs(balls[0].matrix_world.translation.z-(hi+.15))<1e-4,name
 rows.append({'roof':name,'height':height,'radius':radius,'ratio':height/(2*radius),'original_height':o['roof_original_height']})
 cx=(max(v.x for v in p)+min(v.x for v in p))/2;cy=(max(v.y for v in p)+min(v.y for v in p))/2
 for q in related:
  if q.get('castle_asset')!='roof_dormer' or not any(m and m.name=='stone' for m in q.data.materials):continue
  pp=pts(q)
  signed=[math.hypot(v.x-cx,v.y-cy)-radius*(1-(v.z-lo)/height) for v in pp]
  assert min(signed)<0<max(signed),(q.name,signed)
  assert lo<min(v.z for v in pp)<hi,q.name
  dormers.append({'body':q.name,'owner':name,'min_radial_clearance':min(signed),'max_radial_clearance':max(signed)})
assert len(dormers)==0,len(dormers)
assert not any(o.get("castle_asset")=="roof_dormer" for o in s.objects), "roof dormer parts remain"
report={'blender':bpy.app.version_string,'roof_count':len(rows),'dormer_count':len(dormers),'roofs':rows,'dormers':dormers}
args=sys.argv[sys.argv.index('--')+1:];Path(args[0]).write_text(json.dumps(report,indent=2));print('PASS roofs/dormers',len(rows),len(dormers))
