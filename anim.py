# 24h day-cycle animation built on top of castle.blend (day build)
import bpy, math, sys
from pathlib import Path
OUTPUT=Path(__file__).resolve().parent / "output" / "anim"
OUTPUT.mkdir(parents=True, exist_ok=True)
from mathutils import Vector
A=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
MODE=A[0] if A else 'preview'
sc=bpy.context.scene
F0,F1=1,720
sc.frame_start,sc.frame_end=F0,F1;sc.render.fps=24
TODK=[(1,4.0),(60,5.3),(170,7.6),(320,16.4),(430,18.7),(720,28.0)]   # slow dawn/dusk (~4.5 s each), long night
def tod(f):
    for (fa,ha),(fb,hb) in zip(TODK,TODK[1:]):
        if fa<=f<=fb: return ha+(hb-ha)*(f-fa)/(fb-fa)
    return TODK[-1][1]
def sun_dir(f):
    h=tod(f);ang=2*math.pi*(h-6)/24
    el=math.radians(58)*math.sin(ang)                # +58 deg at noon, -58 at midnight
    az=math.pi*.15+ang                                # sun travels east->south->west
    return Vector((math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el))).normalized(),el
def sstep(e0,e1,x):
    t=max(0,min(1,(x-e0)/(e1-e0)));return t*t*(3-2*t)

# ---------------- WORLD: Nishita day + night sky with stars ----------------
w=bpy.data.worlds.new("cycle");sc.world=w;w.use_nodes=True;nt=w.node_tree;nt.nodes.clear()
out=nt.nodes.new("ShaderNodeOutputWorld");bg=nt.nodes.new("ShaderNodeBackground");nt.links.new(bg.outputs[0],out.inputs[0])
sk=nt.nodes.new("ShaderNodeTexSky");sk.sky_type='NISHITA';sk.sun_disc=True;sk.sun_size=math.radians(1.0);sk.sun_intensity=.5;sk.dust_density=1.5;sk.altitude=50
tc=nt.nodes.new("ShaderNodeTexCoord");sep=nt.nodes.new("ShaderNodeSeparateXYZ");nt.links.new(tc.outputs["Generated"],sep.inputs[0])
def M(op,a,b):
    n=nt.nodes.new("ShaderNodeMath");n.operation=op
    for i,v in enumerate((a,b)):
        if isinstance(v,(int,float)): n.inputs[i].default_value=v
        else: nt.links.new(v,n.inputs[i])
    return n.outputs[0]
def MIX(f,a,b,mode='MIX'):
    m=nt.nodes.new("ShaderNodeMix");m.data_type='RGBA';m.blend_type=mode
    for s_,v in (("Factor",f),("A",a),("B",b)):
        if isinstance(v,tuple): m.inputs[s_].default_value=v
        elif isinstance(v,(int,float)): m.inputs[s_].default_value=v
        else: nt.links.new(v,m.inputs[s_])
    return m.outputs["Result"]
# animated scalars live in Value nodes
def VAL(name,v=0.0):
    n=nt.nodes.new("ShaderNodeValue");n.name=name;n.outputs[0].default_value=v;return n
vDay=VAL("day",1);vNight=VAL("night",0);vWarm=VAL("warm",0)
# clouds (projected layer), lit by the sky colour
zc=M('MAXIMUM',sep.outputs["Z"],.02)
cv=nt.nodes.new("ShaderNodeCombineXYZ");nt.links.new(M('DIVIDE',sep.outputs["X"],zc),cv.inputs[0]);nt.links.new(M('DIVIDE',sep.outputs["Y"],zc),cv.inputs[1])
mp=nt.nodes.new("ShaderNodeMapping");nt.links.new(cv.outputs[0],mp.inputs[0])
nz=nt.nodes.new("ShaderNodeTexNoise");nz.inputs["Scale"].default_value=.35;nz.inputs["Detail"].default_value=14;nz.inputs["Roughness"].default_value=.62;nt.links.new(mp.outputs[0],nz.inputs["Vector"])
cm=nt.nodes.new("ShaderNodeMapRange");cm.inputs[1].default_value=.5;cm.inputs[2].default_value=.72;nt.links.new(nz.outputs["Fac"],cm.inputs[0])
hz=nt.nodes.new("ShaderNodeMapRange");hz.inputs[1].default_value=.02;hz.inputs[2].default_value=.12;nt.links.new(sep.outputs["Z"],hz.inputs[0])
cf=M('MULTIPLY',M('MULTIPLY',cm.outputs[0],hz.outputs[0]),.85)
cloudcol=MIX(vDay.outputs[0],(.012,.014,.02,1),(3.6,3.7,3.9,1))          # night clouds dark, day white
cloudcol=MIX(vWarm.outputs[0],cloudcol,MIX(1.0,cloudcol,(1.0,.42,.16,1),'MULTIPLY'))
sky=MIX(cf,sk.outputs[0],cloudcol)
# sunset tint on clouds: multiply by Nishita colour (warms them at dusk)
sky=MIX(M('MULTIPLY',cf,.6),sky,MIX(1.0,sk.outputs[0],cloudcol,'MULTIPLY'))
# below-horizon haze follows day brightness
lo=nt.nodes.new("ShaderNodeMapRange");lo.inputs[1].default_value=-.01;lo.inputs[2].default_value=.15;lo.interpolation_type='SMOOTHSTEP';nt.links.new(sep.outputs["Z"],lo.inputs[0])
haze=MIX(vDay.outputs[0],(.05,.07,.13,1),(3.0,3.3,3.6,1))
haze=MIX(vWarm.outputs[0],haze,MIX(1.0,haze,(1.0,.45,.2,1),'MULTIPLY'))
# warm glow band above the horizon at dawn/dusk
gb_=nt.nodes.new("ShaderNodeMapRange");gb_.inputs[1].default_value=.25;gb_.inputs[2].default_value=0.0;gb_.interpolation_type='SMOOTHSTEP';nt.links.new(sep.outputs["Z"],gb_.inputs[0])
glow=M('MULTIPLY',gb_.outputs[0],vWarm.outputs[0])
sky=MIX(M('MULTIPLY',glow,.55),sky,MIX(1.0,sky,(1.6,.55,.22,1),'MULTIPLY'))
sky=MIX(lo.outputs[0],haze,sky)
# night sky: deep blue gradient + stars
vor=nt.nodes.new("ShaderNodeTexVoronoi");vor.inputs["Scale"].default_value=420;nt.links.new(tc.outputs["Generated"],vor.inputs["Vector"])
st=nt.nodes.new("ShaderNodeMapRange");st.inputs[1].default_value=.11;st.inputs[2].default_value=0.0;nt.links.new(vor.outputs["Distance"],st.inputs[0])
stw=nt.nodes.new("ShaderNodeTexNoise");stw.inputs["Scale"].default_value=60;nt.links.new(tc.outputs["Generated"],stw.inputs["Vector"])
stars=M('MULTIPLY',M('POWER',st.outputs[0],12.0),M('MULTIPLY',stw.outputs["Fac"],2.5))
stars=M('MULTIPLY',stars,M('MULTIPLY',hz.outputs[0],M('SUBTRACT',1.0,cf)))
nightbase=MIX(hz.outputs[0],(.016,.03,.075,1),(.003,.007,.025,1))
starc=nt.nodes.new("ShaderNodeCombineColor");[nt.links.new(stars,starc.inputs[i]) for i in range(3)]
night=MIX(1.0,nightbase,starc.outputs[0],'ADD')
nightK=MIX(vNight.outputs[0],(0,0,0,1),night)
final=MIX(1.0,sky,nightK,'ADD')
nt.links.new(final,bg.inputs["Color"]);bg.inputs["Strength"].default_value=.22
STR=bg  # night colours are pre-scaled by 1/0.22 below
# compensate: night colours were authored for strength 1
for n in nt.nodes:
    pass

# ---------------- LIGHTS ----------------
for o in list(bpy.data.objects):
    if o.type=='LIGHT' and o.data.type=='SUN': bpy.data.objects.remove(o)
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.name="SunLamp";sun.data.angle=math.radians(2)
bpy.ops.object.light_add(type='SUN');moon=bpy.context.object;moon.name="MoonLamp";moon.data.color=(.62,.72,1.0);moon.data.angle=math.radians(1)
# soft cool sky fill so the shadow side of the castle stays readable at night (fixed direction, no shadows)
bpy.ops.object.light_add(type='SUN');mfill=bpy.context.object;mfill.name="MoonFill";mfill.data.color=(.45,.55,.95);mfill.data.angle=math.radians(30)
mfill.data.cycles.cast_shadow=False
_fa=1.395+.22+math.pi;_fe=math.radians(35)
mfill.rotation_euler=(-Vector((math.cos(_fe)*math.cos(_fa),math.cos(_fe)*math.sin(_fa),math.sin(_fe)))).to_track_quat('-Z','Y').to_euler()
# moon disc
bpy.ops.mesh.primitive_uv_sphere_add(radius=150,segments=48,ring_count=24);md=bpy.context.object;md.name="MoonDisc"
mm=bpy.data.materials.new("moonmat");mm.use_nodes=True;n2=mm.node_tree;n2.nodes.clear()
mo_=n2.nodes.new("ShaderNodeOutputMaterial");em=n2.nodes.new("ShaderNodeEmission");nn=n2.nodes.new("ShaderNodeTexNoise");nn.inputs["Scale"].default_value=3;nn.inputs["Detail"].default_value=8
rr=n2.nodes.new("ShaderNodeValToRGB");rr.color_ramp.elements[0].color=(.5,.5,.48,1);rr.color_ramp.elements[1].color=(1,.98,.9,1)
n2.links.new(nn.outputs["Fac"],rr.inputs[0]);n2.links.new(rr.outputs[0],em.inputs[0]);n2.links.new(em.outputs[0],mo_.inputs[0])
md.data.materials.append(mm);md.visible_shadow=False;md.visible_volume_scatter=False
for o in bpy.data.objects:
    if o.name.startswith("SurfMist"): o.hide_render=True     # speed
# warm interior lights at night
WL=[]
for p in [(2,-1.5,16),(-3,4,13),(4,4,28),(3,-14.5,6),(-3,1,23),(-4,10,9),(9,6,12)]:
    bpy.ops.object.light_add(type='POINT',location=(p[0]+1,p[1],p[2]+3.6));l=bpy.context.object;l.data.color=(1,.5,.18);l.data.shadow_soft_size=1.0;WL.append(l)
glass=bpy.data.materials.get("glass");gb=glass.node_tree.nodes["Principled BSDF"]
win=bpy.data.materials.get("win")

# ---------------- OCEAN time ----------------
ocean=[o for o in bpy.data.objects if any(m.type=='OCEAN' for m in o.modifiers)][0]
om=[m for m in ocean.modifiers if m.type=='OCEAN'][0]
om.wave_scale=8.0
om.time=0;om.keyframe_insert('time',frame=F0);om.time=30.0;om.keyframe_insert('time',frame=F1)
for fc in ocean.animation_data.action.fcurves:
    for k in fc.keyframe_points: k.interpolation='LINEAR'

# ---------------- PER-FRAME KEYS for lighting ----------------
D=5000
for f in range(F0,F1+1,6):
    sd,el=sun_dir(f)
    day=sstep(math.radians(-6),math.radians(8),el)           # 0 at civil twilight -> 1 in daylight
    nightf=1-sstep(math.radians(-10),math.radians(2),el)
    sk.sun_elevation=el;sk.sun_rotation=math.atan2(sd.x,sd.y)
    sk.keyframe_insert('sun_elevation',frame=f);sk.keyframe_insert('sun_rotation',frame=f)
    vDay.outputs[0].default_value=day;vDay.outputs[0].keyframe_insert('default_value',frame=f)
    vNight.outputs[0].default_value=nightf*4.5;vNight.outputs[0].keyframe_insert('default_value',frame=f)
    sun.rotation_euler=(-sd).to_track_quat('-Z','Y').to_euler('XYZ',sun.rotation_euler);sun.keyframe_insert('rotation_euler',frame=f)
    warm=1-sstep(math.radians(2),math.radians(20),el)          # low sun -> warmer
    wglow=sstep(math.radians(-9),math.radians(-1),el)*(1-sstep(math.radians(4),math.radians(16),el))
    vWarm.outputs[0].default_value=wglow;vWarm.outputs[0].keyframe_insert('default_value',frame=f)
    sun.data.color=(1,.95-.5*warm,.87-.7*warm);sun.data.keyframe_insert('color',frame=f)
    sun.data.energy=4.0*sstep(math.radians(-2),math.radians(10),el);sun.data.keyframe_insert('energy',frame=f)
    MAZ=1.395+.22;mel=math.radians(9+3*sstep(430,720,f))
    md_=Vector((math.cos(mel)*math.cos(MAZ),math.cos(mel)*math.sin(MAZ),math.sin(mel)))
    md.location=md_*D;md.keyframe_insert('location',frame=f)
    md.hide_render=False
    em.inputs[1].default_value=14*nightf+0.0;em.inputs[1].keyframe_insert('default_value',frame=f)
    moon.rotation_euler=(-md_).to_track_quat('-Z','Y').to_euler('XYZ',moon.rotation_euler);moon.keyframe_insert('rotation_euler',frame=f)
    moon.data.energy=4.5*nightf;moon.data.keyframe_insert('energy',frame=f)
    mfill.data.energy=1.1*nightf;mfill.data.keyframe_insert('energy',frame=f)
    for l in WL:
        l.data.energy=900*nightf;l.data.keyframe_insert('energy',frame=f)
    gb.inputs["Emission Strength"].default_value=6*nightf;gb.inputs["Emission Strength"].keyframe_insert('default_value',frame=f)
    sc.view_settings.exposure=1.75*nightf+0.25*(1-day)*(1-nightf);sc.view_settings.keyframe_insert('exposure',frame=f)

# ---------------- CAMERA: one continuous eased path ----------------
def lerp(a,b,t): return a+(b-a)*t
def ease(t): return t*t*(3-2*t)
# control points: (frame, radius, height, target z, lens)
CP=[(1,135,14,16,38),(150,120,20,16,38),(250,45,30,22,28),(330,42,22,18,26),(410,62,6.5,15,24),(490,70,7.5,16,26),
    (560,115,85,6,30),(640,125,40,12,34),(720,135,14,16,38)]
def camstate(f):
    for (fa,ra,ha,ta,la),(fb,rb,hb,tb,lb) in zip(CP,CP[1:]):
        if fa<=f<=fb:
            t=ease((f-fa)/(fb-fa));return lerp(ra,rb,t),lerp(ha,hb,t),lerp(ta,tb,t),lerp(la,lb,t)
    return CP[-1][1:]
cam=bpy.data.objects.new("CamOrbit",bpy.data.cameras.new("CamOrbit"));sc.collection.objects.link(cam);cam.data.clip_end=20000
tgt=bpy.data.objects.new("CamTarget",None);sc.collection.objects.link(tgt)
c=cam.constraints.new('TRACK_TO');c.target=tgt;c.track_axis='TRACK_NEGATIVE_Z';c.up_axis='UP_Y'
for f in range(F0,F1+1,4):
    R,H,TZ,LENS=camstate(f)
    th=-math.pi/2+2*math.pi*(f-F0)/(F1-F0)      # starts on the gate side, one full orbit
    cam.location=(1+R*math.cos(th),R*math.sin(th),H);cam.keyframe_insert('location',frame=f)
    tgt.location=(1,2,TZ);tgt.keyframe_insert('location',frame=f)
    cam.data.lens=LENS;cam.data.keyframe_insert('lens',frame=f)
sc.camera=cam

sea=bpy.data.materials["sea"].node_tree
for n in sea.nodes:
    if n.type=='MAP_RANGE' and abs(n.inputs[3].default_value-.95)<1e-4 and abs(n.inputs[4].default_value-.5)<1e-4:
        n.inputs[3].default_value=2.0;n.inputs[4].default_value=2.0
for n in sea.nodes:
    if n.type=='MATH' and n.operation=='MINIMUM' and abs(n.inputs[1].default_value-.85)<1e-4: n.inputs[1].default_value=0.0
    if n.type=='MATH' and n.operation=='SUBTRACT' and abs(n.inputs[1].default_value-.75)<1e-4: n.inputs[1].default_value=5.0   # no open-sea whitecap 'snow'
# ---------------- RENDER SETTINGS ----------------
sc.render.engine='CYCLES';sc.cycles.use_denoising=True;sc.cycles.denoiser='OPENIMAGEDENOISE'
sc.cycles.seed=0;sc.cycles.use_animated_seed=False
sc.cycles.adaptive_threshold=.02;sc.cycles.adaptive_min_samples=16
sc.cycles.sample_clamp_direct=8;sc.cycles.sample_clamp_indirect=2;sc.cycles.blur_glossy=1.0
sc.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL';sc.cycles.denoising_prefilter='ACCURATE'
# spray droplets / splash sheets sparkle -> hide; soften shoreline foam
for o in bpy.data.objects:
    if o.name.startswith(("Drops","Splash")): o.hide_render=True
sc.render.use_persistent_data=True;sc.cycles.max_bounces=4;sc.cycles.use_adaptive_sampling=True
if MODE=='preview':
    sc.render.resolution_x,sc.render.resolution_y=640,360;sc.cycles.samples=8;sc.frame_step=4
    sc.render.filepath=str(OUTPUT / "preview/f_")
elif MODE=='keys':
    sc.render.resolution_x,sc.render.resolution_y=640,360;sc.cycles.samples=12
else:
    sc.render.resolution_x,sc.render.resolution_y=(int(A[3]),int(A[4])) if len(A)>4 else (1280,720);sc.cycles.samples=int(A[1]) if len(A)>1 else 32;sc.frame_step=int(A[2]) if len(A)>2 else 1
    sc.render.filepath=(A[5] if len(A)>5 else str(OUTPUT / "final/f_"))
    if len(A)>7: sc.frame_start,sc.frame_end=int(A[6]),int(A[7])
sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc.render.use_overwrite=False;sc.render.use_placeholder=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "castle_24h.blend"))
KEYS=A[1:] if MODE=='keys' and len(A)>1 else ['dawn1:110','dawn2:140','noon:245','dusk1:380','dusk2:410','night545:545','midnight:600','moon:700','flyby:290']
if MODE=='keys':
    # dawn ~06:00, noon, dusk ~18:00, midnight, plus fly-by & aerial
    for name,f in [(n_,int(f_)) for n_,f_ in (x.split(":") for x in KEYS)]:
        sc.frame_set(f);sc.render.filepath=str(OUTPUT / f"keys/{name}_{f:03d}.png");bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
