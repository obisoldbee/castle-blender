"""Diagnostic renders only. Does not save/alter input blend on disk."""
import bpy,sys,json
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]);out.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene
assert s.camera, 'Release must have an active camera'
s.render.resolution_x=480;s.render.resolution_y=270;s.render.resolution_percentage=100
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8;s.cycles.use_denoising=False
s.render.threads_mode='FIXED';s.render.threads=4
s.render.image_settings.file_format='PNG';s.render.use_placeholder=False;s.render.use_overwrite=True
frames=[int(f) for f in args[1:]] or [1]
for f in frames:
 s.frame_set(f);s.render.filepath=str(out/f'frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
print('CHECK_RENDERS',frames)
