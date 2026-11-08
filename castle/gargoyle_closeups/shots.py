import bpy,sys,math
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUTPUT=BASE.parent / "output" / "gargoyle_closeups"
OUTPUT.mkdir(parents=True, exist_ok=True)
from mathutils import Vector
sys.path.insert(0,str(BASE / 'fix'));import gargfix;gargfix.apply()
TS=__import__('os').environ.get('TS','')
a=sys.argv[sys.argv.index('--')+1:]
spp=int(a[0]); only=(a[1] if len(a)>1 and a[1]!="all" else None)
s=bpy.context.scene;s.render.use_overwrite=True;s.render.use_placeholder=False
for o in s.objects:
    if o.type=='CAMERA' and o.animation_data: pass
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
for n,(t,off,lens,fr) in SH.items():
    if only and only!=n: continue
    cd=bpy.data.cameras.new(n);cd.lens=lens;cd.clip_start=.05
    cd.dof.use_dof=True;cd.dof.focus_distance=off.length;cd.dof.aperture_fstop=5.6
    c=bpy.data.objects.new(n,cd);s.collection.objects.link(c)
    c.location=t+off;c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler()
    s.camera=c;s.frame_set(fr)
    if 'dusk' in n: s.view_settings.exposure+=0.6
    s.render.resolution_x=1600;s.render.resolution_y=1000;s.render.resolution_percentage=int(a[2]) if len(a)>2 else 100
    s.cycles.samples=spp;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True
    s.render.filepath=str(OUTPUT / f'{n}_fixed_{TS}.png')
    bpy.ops.render.render(write_still=True)
