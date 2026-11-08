"""Prepare close-up cameras or explicitly render to a chosen output directory."""
import argparse, bpy, sys, math
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent

def parse_options(argv):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('samples',nargs='?',type=int,default=64)
    p.add_argument('shot',nargs='?',default='all',choices=('all','g1_threequarter_day','g2_profile_day','g3_from_below','g4_dusk'))
    p.add_argument('percentage',nargs='?',type=int,default=100)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--mode',choices=('prepare','render'),default='prepare')
    p.add_argument('--force',action='store_true')
    p.add_argument('--no-denoise',action='store_true')
    o=p.parse_args(argv)
    if o.samples<1: p.error('samples must be positive')
    if not 1<=o.percentage<=100: p.error('percentage must be between 1 and 100')
    o.output_dir=o.output_dir.expanduser().resolve()
    return o

opt=parse_options(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
def head(cx,cy,cz,ang,d): return Vector((cx+math.cos(ang)*d,cy+math.sin(ang)*d,cz+.3))
t3=head(15.28,5.02,19.8,0,.7)
t1=head(2.11,.82,31.26,-math.pi/2-.55,1.0)-Vector((math.cos(-math.pi/2-.55),math.sin(-math.pi/2-.55),0))*2.6*.12   # great tower, sea side
t2=head(15.28,-0.98,19.8,0,.7)                 # buttress pier east
SH={ # name: (target, cam offset, lens, frame)
 'g1_threequarter_day':(t1,Vector((1.8,-5.8,1.4)),75,250),
 'g2_profile_day':(t2,Vector((0.6,-5.0,0.4)),70,250),
 'g3_from_below':(t3+Vector((-0.3,0,-0.8)),Vector((2.0,1.8,-1.6)),30,230),
 'g4_dusk':(t1+Vector((0.45,0.75,-0.1)),Vector((4.5,-4.5,0.4)),50,385),
}

selected={n:v for n,v in SH.items() if opt.shot in ('all',n)}
if opt.mode=='render' and not opt.force and any((opt.output_dir/(n+'.png')).exists() for n in selected):
    raise FileExistsError('Output exists; choose a new directory or explicit --force')
s=bpy.context.scene
# Fail before any patch/camera edits if a conflicting named object is present.
for n in selected:
    if bpy.data.objects.get(n) and bpy.data.objects[n].type!='CAMERA':
        raise RuntimeError('Non-camera object already uses shot name: '+n)
sys.path.insert(0,str(BASE/'fix'))
import gargfix
gargfix.apply()
opt.output_dir.mkdir(parents=True,exist_ok=True)
original=(s.camera,s.frame_current,s.view_settings.exposure,s.render.filepath,
          s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,
          s.cycles.samples,s.cycles.use_denoising,s.cycles.use_adaptive_sampling)
try:
    for n,(t,off,lens,fr) in selected.items():
        c=bpy.data.objects.get(n)
        if c is None:
            c=bpy.data.objects.new(n,bpy.data.cameras.new(n));s.collection.objects.link(c)
        cd=c.data;cd.lens=lens;cd.clip_start=.05
        cd.dof.use_dof=True;cd.dof.focus_distance=off.length;cd.dof.aperture_fstop=5.6
        c.location=t+off;c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler()
        if opt.mode!='render': continue
        s.camera=c
        # Reset only the unanimated fallback, then evaluate the target frame.
        # Animated day/night exposure must take precedence over the entry frame.
        s.view_settings.exposure=original[2];s.frame_set(fr)
        s.view_settings.exposure+=(.6 if 'dusk' in n else 0)
        s.render.resolution_x=1600;s.render.resolution_y=1000;s.render.resolution_percentage=opt.percentage
        s.cycles.samples=opt.samples;s.cycles.use_denoising=not opt.no_denoise;s.cycles.use_adaptive_sampling=True
        s.render.filepath=str(opt.output_dir/(n+'.png'))
        bpy.ops.render.render(write_still=True)
finally:
    s.camera=original[0];s.frame_set(original[1]);s.view_settings.exposure=original[2]
    s.render.filepath=original[3];s.render.resolution_x=original[4];s.render.resolution_y=original[5]
    s.render.resolution_percentage=original[6];s.cycles.samples=original[7]
    s.cycles.use_denoising=original[8];s.cycles.use_adaptive_sampling=original[9]
