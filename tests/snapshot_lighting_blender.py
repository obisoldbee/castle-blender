"""Read-only sampled lighting/exposure/camera regression snapshot."""
import bpy,json,sys
from pathlib import Path
s=bpy.context.scene;rows={}
for f in [1,110,245,385,560,720]:
 s.frame_set(f);s.view_layers[0].update()
 lights={o.name:{'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'}
 c=s.camera.evaluated_get(bpy.context.evaluated_depsgraph_get())
 rows[str(f)]={'exposure':s.view_settings.exposure,'lights':lights,'camera':list(c.matrix_world.translation),'lens':c.data.lens,'moon':list(bpy.data.objects['MoonDisc'].location)}
args=sys.argv[sys.argv.index('--')+1:];Path(args[0]).write_text(json.dumps(rows,indent=2));print('LIGHTING_SNAPSHOT')
