import bpy
from pathlib import Path
from mathutils import Vector
D=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(D/'Night_Queen_Local_Corrections_v02.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=40;s.cycles.use_denoising=False
c=s.camera;c.data.type='ORTHO';c.data.ortho_scale=3.55;c.location=(3,-7,2.8);c.rotation_euler=(Vector((0,0,1.75))-c.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=750;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.filepath=str(D/'renders/verified_full_oblique.png');bpy.ops.render.render(write_still=True)
