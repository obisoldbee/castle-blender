import bpy, bmesh, math, random, sys
from mathutils import Vector
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
from pathlib import Path
OUT=str(Path(__file__).resolve().parent / "output") + "/"
Path(OUT).mkdir(parents=True, exist_ok=True)

def mat(name,col,rough=0.8,emit=None,es=0,noise=True,bump=0.4):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(*col,1);b.inputs["Roughness"].default_value=rough
    if noise:
        tc=nt.nodes.new("ShaderNodeTexCoord");n=nt.nodes.new("ShaderNodeTexNoise");n.inputs["Scale"].default_value=6;n.inputs["Detail"].default_value=8
        nt.links.new(tc.outputs["Object"],n.inputs["Vector"])
        r=nt.nodes.new("ShaderNodeValToRGB");r.color_ramp.elements[0].color=(col[0]*.5,col[1]*.5,col[2]*.5,1);r.color_ramp.elements[1].color=(col[0]*1.3,col[1]*1.3,col[2]*1.3,1)
        nt.links.new(n.outputs["Fac"],r.inputs["Fac"]);nt.links.new(r.outputs["Color"],b.inputs["Base Color"])
        # brick-ish bump
        bk=nt.nodes.new("ShaderNodeTexBrick");bk.inputs["Scale"].default_value=3;bk.inputs["Mortar Size"].default_value=.03
        nt.links.new(tc.outputs["Object"],bk.inputs["Vector"])
        bp=nt.nodes.new("ShaderNodeBump");bp.inputs["Strength"].default_value=bump
        mx=nt.nodes.new("ShaderNodeMath");mx.operation='ADD';nt.links.new(bk.outputs["Fac"],mx.inputs[0]);nt.links.new(n.outputs["Fac"],mx.inputs[1])
        nt.links.new(mx.outputs[0],bp.inputs["Height"]);nt.links.new(bp.outputs["Normal"],b.inputs["Normal"])
    if emit:
        b.inputs["Emission Color"].default_value=(*emit,1);b.inputs["Emission Strength"].default_value=es
    return m
ARGS=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
DAY=('--night' not in ARGS)
ARGS=[a for a in ARGS if not a.startswith('--')]
SAMPLES=int(ARGS[0]) if ARGS else 64
ONLY=ARGS[1:]
PFX="day_" if DAY else "render_"
ZW=3.6  # plateau height (world)

def N(nt,t,**kw):
    n=nt.nodes.new(t)
    for k,v in kw.items():
        if k in n.inputs: n.inputs[k].default_value=v
        else: setattr(n,k,v)
    return n
def L(nt,a,b): nt.links.new(a,b)
def math_(nt,op,a,b=None,v=None):
    n=nt.nodes.new("ShaderNodeMath");n.operation=op
    if isinstance(a,(int,float)): n.inputs[0].default_value=a
    else: L(nt,a,n.inputs[0])
    if b is not None:
        if isinstance(b,(int,float)): n.inputs[1].default_value=b
        else: L(nt,b,n.inputs[1])
    return n.outputs[0]
def mixc(nt,f,a,b):
    m=nt.nodes.new("ShaderNodeMix");m.data_type='RGBA'
    for s,v in (("Factor",f),("A",a),("B",b)):
        if isinstance(v,tuple): m.inputs[s].default_value=v if len(v)==4 else (*v,1)
        elif isinstance(v,(int,float)): m.inputs[s].default_value=v
        else: L(nt,v,m.inputs[s])
    return m.outputs["Result"]
def grime(nt,pos,base_col,zmin=0.0):
    """streaks + moss/dirt band near world base"""
    sep=N(nt,"ShaderNodeSeparateXYZ");L(nt,pos,sep.inputs[0])
    mp=N(nt,"ShaderNodeMapping");mp.inputs["Scale"].default_value=(2,2,.12);L(nt,pos,mp.inputs[0])
    st=N(nt,"ShaderNodeTexNoise",Scale=2.0,Detail=6.0);L(nt,mp.outputs[0],st.inputs["Vector"])
    streak=N(nt,"ShaderNodeMapRange");streak.inputs[1].default_value=.38;streak.inputs[2].default_value=.72;streak.inputs[3].default_value=1.05;streak.inputs[4].default_value=.3
    L(nt,st.outputs["Fac"],streak.inputs[0])
    c=mixc(nt,1.0,base_col,(0,0,0,1));c.node.blend_type='MULTIPLY'
    L(nt,streak.outputs[0],c.node.inputs["Factor"]);
    # use: color*streak  -> do multiply properly
    mulc=nt.nodes.new("ShaderNodeMix");mulc.data_type='RGBA';mulc.blend_type='MULTIPLY';mulc.inputs["Factor"].default_value=1
    L(nt,base_col,mulc.inputs["A"]);cv=N(nt,"ShaderNodeCombineColor");L(nt,streak.outputs[0],cv.inputs[0]);L(nt,streak.outputs[0],cv.inputs[1]);L(nt,streak.outputs[0],cv.inputs[2]);L(nt,cv.outputs[0],mulc.inputs["B"])
    col=mulc.outputs["Result"]
    nz=N(nt,"ShaderNodeTexNoise",Scale=1.5,Detail=8.0);L(nt,pos,nz.inputs["Vector"])
    h=N(nt,"ShaderNodeMapRange");h.inputs[1].default_value=ZW+zmin;h.inputs[2].default_value=ZW+zmin+2.8;h.inputs[3].default_value=1;h.inputs[4].default_value=0
    L(nt,sep.outputs["Z"],h.inputs[0])
    m=math_(nt,'MULTIPLY',h.outputs[0],math_(nt,'MULTIPLY',nz.outputs["Fac"],1.8))
    m=math_(nt,'MINIMUM',m,1.0)
    dirt=mixc(nt,m,col,(.035,.032,.022,1))
    # moss patches
    mn=N(nt,"ShaderNodeTexNoise",Scale=4.0,Detail=10.0);L(nt,pos,mn.inputs["Vector"])
    mm=N(nt,"ShaderNodeMapRange");mm.inputs[1].default_value=.55;mm.inputs[2].default_value=.7;L(nt,mn.outputs["Fac"],mm.inputs[0])
    mf=math_(nt,'MULTIPLY',mm.outputs[0],h.outputs[0])
    return mixc(nt,mf,dirt,(.035,.055,.018,1)),m

def stone_mat(name,c1,c2,mortar,scale=1.0,bw=.62,rh=.3):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes["Principled BSDF"]
    geo=N(nt,"ShaderNodeNewGeometry");pos=geo.outputs["Position"]
    sep=N(nt,"ShaderNodeSeparateXYZ");L(nt,pos,sep.inputs[0])
    sn=N(nt,"ShaderNodeSeparateXYZ");L(nt,geo.outputs["Normal"],sn.inputs[0])
    outs=[];rids=[]
    for horiz in ("X","Y"):
        cv=N(nt,"ShaderNodeCombineXYZ");L(nt,sep.outputs[horiz],cv.inputs[0]);L(nt,sep.outputs["Z"],cv.inputs[1])
        # distort slightly for hand-cut feel
        bk=N(nt,"ShaderNodeTexBrick",offset=.42,offset_frequency=2,squash=.62,squash_frequency=3);bk.inputs["Scale"].default_value=scale
        bk.inputs["Brick Width"].default_value=bw;bk.inputs["Row Height"].default_value=rh;bk.inputs["Mortar Size"].default_value=.022;bk.inputs["Mortar Smooth"].default_value=.75
        bk.inputs["Bias"].default_value=0
        bk.inputs["Color1"].default_value=(*c1,1);bk.inputs["Color2"].default_value=(*c2,1);bk.inputs["Mortar"].default_value=(*mortar,1)
        L(nt,cv.outputs[0],bk.inputs["Vector"]);outs.append(bk)
        bk2=N(nt,"ShaderNodeTexBrick",offset=.42,offset_frequency=2,squash=.62,squash_frequency=3);bk2.inputs["Scale"].default_value=scale
        bk2.inputs["Brick Width"].default_value=bw;bk2.inputs["Row Height"].default_value=rh;bk2.inputs["Mortar Size"].default_value=0;bk2.inputs["Bias"].default_value=0
        bk2.inputs["Color1"].default_value=(0,0,0,1);bk2.inputs["Color2"].default_value=(1,1,1,1);L(nt,cv.outputs[0],bk2.inputs["Vector"]);rids.append(bk2)
    an=math_(nt,'ABSOLUTE',sn.outputs["X"]);anY=math_(nt,'ABSOLUTE',sn.outputs["Y"])
    w=math_(nt,'GREATER_THAN',anY,an)   # 1 -> wall faces Y -> use X horiz
    colA=outs[0].outputs["Color"];colB=outs[1].outputs["Color"]
    col=mixc(nt,w,colB,colA)
    fac=N(nt,"ShaderNodeMix");fac.data_type='FLOAT';L(nt,w,fac.inputs["Factor"]);L(nt,outs[1].outputs["Fac"],fac.inputs[2]);L(nt,outs[0].outputs["Fac"],fac.inputs[3])
    mortarF=fac.outputs[0]
    # per-stone surface noise
    nz=N(nt,"ShaderNodeTexNoise",Scale=9.0,Detail=10.0,Roughness=.65);L(nt,pos,nz.inputs["Vector"])
    vn=N(nt,"ShaderNodeTexVoronoi",feature='DISTANCE_TO_EDGE');vn.inputs["Scale"].default_value=6;L(nt,pos,vn.inputs["Vector"])
    rid=N(nt,"ShaderNodeMix");rid.data_type='RGBA';L(nt,w,rid.inputs["Factor"]);L(nt,rids[1].outputs["Color"],rid.inputs["A"]);L(nt,rids[0].outputs["Color"],rid.inputs["B"])
    rbw=N(nt,"ShaderNodeRGBToBW");L(nt,rid.outputs["Result"],rbw.inputs[0]);RND=rbw.outputs[0]
    hr=N(nt,"ShaderNodeValToRGB");E=hr.color_ramp.elements;E[0].color=(.62,.55,.42,1);E[1].color=(.42,.44,.47,1);e=E.new(.5);e.color=(.5,.5,.48,1);e=E.new(.8);e.color=(.36,.33,.3,1)
    L(nt,RND,hr.inputs[0])
    col=mixc(nt,.55,col,hr.outputs["Color"]);col.node.blend_type='OVERLAY'
    MISS=math_(nt,'GREATER_THAN',RND,.988)
    col=mixc(nt,math_(nt,'MULTIPLY',MISS,.55),col,(.07,.062,.055,1))
    tint=mixc(nt,.6,col,nz.outputs["Color"]);tint.node.blend_type='OVERLAY'
    gcol,dirtF=grime(nt,pos,tint)
    L(nt,gcol,b.inputs["Base Color"]);b.inputs["Roughness"].default_value=.88
    # bump: mortar recessed, chipped edges, pitted surface
    chip=math_(nt,'MULTIPLY',vn.outputs["Distance"],0.0)
    # per-block relief from brick colour id, chipped arrises from noisy mortar edge
    bid=N(nt,"ShaderNodeMix");bid.data_type='RGBA';L(nt,w,bid.inputs["Factor"]);bid.inputs["A"].default_value=(0,0,0,1)
    b2=[]
    for bk_ in outs:
        bw_=N(nt,"ShaderNodeRGBToBW");L(nt,bk_.outputs["Color"],bw_.inputs[0]);b2.append(bw_.outputs[0])
    relief=N(nt,"ShaderNodeMix");relief.data_type='FLOAT';L(nt,w,relief.inputs["Factor"]);L(nt,b2[1],relief.inputs[2]);L(nt,b2[0],relief.inputs[3])
    cn=N(nt,"ShaderNodeTexNoise",Scale=14.0,Detail=8.0,Roughness=.7);L(nt,pos,cn.inputs["Vector"])
    edge=math_(nt,'MINIMUM',math_(nt,'MULTIPLY',math_(nt,'ADD',mortarF,math_(nt,'MULTIPLY',cn.outputs["Fac"],.8)),1.3),1.0)
    hgt=math_(nt,'ADD',math_(nt,'MULTIPLY',nz.outputs["Fac"],.35),math_(nt,'MULTIPLY',relief.outputs[0],1.6))
    hgt=math_(nt,'SUBTRACT',hgt,math_(nt,'MULTIPLY',edge,1.2))
    hgt=math_(nt,'SUBTRACT',hgt,math_(nt,'MULTIPLY',MISS,1.6))
    hgt=math_(nt,'ADD',hgt,math_(nt,'MULTIPLY',RND,.6))
    bp=N(nt,"ShaderNodeBump",Strength=.75,Distance=.06);L(nt,hgt,bp.inputs["Height"]);L(nt,bp.outputs["Normal"],b.inputs["Normal"])
    return m

def slate_mat(name,pitched=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes["Principled BSDF"]
    tc=N(nt,"ShaderNodeTexCoord");sep=N(nt,"ShaderNodeSeparateXYZ");L(nt,tc.outputs["Object"],sep.inputs[0])
    ang=math_(nt,'ARCTAN2',sep.outputs["Y"],sep.outputs["X"])
    rad=N(nt,"ShaderNodeVectorMath",operation='LENGTH');cxy=N(nt,"ShaderNodeCombineXYZ");L(nt,sep.outputs["X"],cxy.inputs[0]);L(nt,sep.outputs["Y"],cxy.inputs[1]);L(nt,cxy.outputs[0],rad.inputs[0])
    u=math_(nt,'MULTIPLY',ang,math_(nt,'MAXIMUM',rad.outputs["Value"],.3))
    cv=N(nt,"ShaderNodeCombineXYZ")
    if pitched:   # cube rotated 45deg about Y: ridge along local Y, slope along (x+z)
        L(nt,math_(nt,'MULTIPLY',sep.outputs["Y"],3.2),cv.inputs[0])
        vv=math_(nt,'MULTIPLY',math_(nt,'ADD',sep.outputs["X"],sep.outputs["Z"]),3.4)
        L(nt,vv,cv.inputs[1])
    else:
        L(nt,u,cv.inputs[0]);L(nt,sep.outputs["Z"],cv.inputs[1])
    bk=N(nt,"ShaderNodeTexBrick",offset=.5);bk.inputs["Scale"].default_value=1;bk.inputs["Brick Width"].default_value=.28;bk.inputs["Row Height"].default_value=.17
    bk.inputs["Mortar Size"].default_value=.008;bk.inputs["Bias"].default_value=0
    bk.inputs["Color1"].default_value=(.045,.05,.06,1);bk.inputs["Color2"].default_value=(.11,.11,.12,1);bk.inputs["Mortar"].default_value=(.01,.01,.012,1)
    L(nt,cv.outputs[0],bk.inputs["Vector"])
    nz=N(nt,"ShaderNodeTexNoise",Scale=14.0,Detail=6.0);L(nt,tc.outputs["Object"],nz.inputs["Vector"])
    lich=N(nt,"ShaderNodeTexNoise",Scale=6.0,Detail=10.0);L(nt,tc.outputs["Object"],lich.inputs["Vector"])
    lm=N(nt,"ShaderNodeMapRange");lm.inputs[1].default_value=.6;lm.inputs[2].default_value=.72;L(nt,lich.outputs["Fac"],lm.inputs[0])
    col=mixc(nt,lm.outputs[0],bk.outputs["Color"],(.16,.15,.1,1))
    L(nt,col,b.inputs["Base Color"])
    rr=N(nt,"ShaderNodeMapRange");rr.inputs[3].default_value=.35;rr.inputs[4].default_value=.7;L(nt,nz.outputs["Fac"],rr.inputs[0]);L(nt,rr.outputs[0],b.inputs["Roughness"])
    # tile lip: gradient inside each row via fract(z/rh)
    fr=math_(nt,'FRACT',math_(nt,'DIVIDE',(vv if pitched else sep.outputs["Z"]),.17))
    hgt=math_(nt,'SUBTRACT',math_(nt,'MULTIPLY',fr,.6),bk.outputs["Fac"])
    hgt=math_(nt,'ADD',hgt,math_(nt,'MULTIPLY',nz.outputs["Fac"],.2))
    bp=N(nt,"ShaderNodeBump",Strength=.8,Distance=.03);L(nt,hgt,bp.inputs["Height"]);L(nt,bp.outputs["Normal"],b.inputs["Normal"])
    return m

def rock_mat(name,wscale=.5,wdist=4.5,bdir='Z',vscale=.45):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes["Principled BSDF"]
    geo=N(nt,"ShaderNodeNewGeometry");pos=geo.outputs["Position"];sep=N(nt,"ShaderNodeSeparateXYZ");L(nt,pos,sep.inputs[0])
    sn=N(nt,"ShaderNodeSeparateXYZ");L(nt,geo.outputs["Normal"],sn.inputs[0])
    # strata bands along Z, warped
    wv=N(nt,"ShaderNodeTexWave",wave_type='BANDS',bands_direction=bdir);wv.inputs["Scale"].default_value=wscale;wv.inputs["Distortion"].default_value=wdist;wv.inputs["Detail"].default_value=6;wv.inputs["Detail Scale"].default_value=1.5
    L(nt,pos,wv.inputs["Vector"])
    cr=N(nt,"ShaderNodeValToRGB");E=cr.color_ramp.elements
    E[0].position=0;E[0].color=(.09,.08,.07,1);E[1].position=1;E[1].color=(.26,.23,.19,1)
    e=E.new(.4);e.color=(.17,.15,.13,1);e=E.new(.6);e.color=(.12,.11,.1,1);e=E.new(.8);e.color=(.3,.27,.22,1)
    L(nt,wv.outputs["Fac"],cr.inputs[0])
    nz=N(nt,"ShaderNodeTexNoise",Scale=2.0,Detail=12.0,Roughness=.65);L(nt,pos,nz.inputs["Vector"])
    fn=N(nt,"ShaderNodeTexNoise",Scale=25.0,Detail=8.0);L(nt,pos,fn.inputs["Vector"])
    col=mixc(nt,.4,cr.outputs["Color"],nz.outputs["Color"]);col.node.blend_type='OVERLAY'
    # cracks
    vn=N(nt,"ShaderNodeTexVoronoi",feature='DISTANCE_TO_EDGE');vn.inputs["Scale"].default_value=vscale;vn.inputs["Randomness"].default_value=1
    mp=N(nt,"ShaderNodeMapping");mp.inputs["Scale"].default_value=(1,1,2.5);L(nt,pos,mp.inputs[0]);L(nt,mp.outputs[0],vn.inputs["Vector"])
    crack=N(nt,"ShaderNodeMapRange");crack.inputs[1].default_value=0;crack.inputs[2].default_value=.012;crack.inputs[3].default_value=1;crack.inputs[4].default_value=0;L(nt,vn.outputs["Distance"],crack.inputs[0])
    col=mixc(nt,crack.outputs[0],col,(.02,.018,.015,1))
    # flat tops get grass/lichen
    up=N(nt,"ShaderNodeMapRange");up.inputs[1].default_value=.75;up.inputs[2].default_value=.92;L(nt,sn.outputs["Z"],up.inputs[0])
    col=mixc(nt,math_(nt,'MULTIPLY',up.outputs[0],math_(nt,'GREATER_THAN',sep.outputs["Z"],2.5)),col,(.06,.075,.03,1))
    # wet dark tide zone + algae
    wet=N(nt,"ShaderNodeMapRange");wet.inputs[1].default_value=.5;wet.inputs[2].default_value=2.6;wet.inputs[3].default_value=1;wet.inputs[4].default_value=0;L(nt,sep.outputs["Z"],wet.inputs[0])
    wetn=math_(nt,'MINIMUM',math_(nt,'MULTIPLY',wet.outputs[0],math_(nt,'ADD',fn.outputs["Fac"],.6)),1.0)
    col=mixc(nt,wetn,col,(.03,.035,.02,1))
    L(nt,col,b.inputs["Base Color"])
    rough=N(nt,"ShaderNodeMapRange");rough.inputs[3].default_value=.92;rough.inputs[4].default_value=.35;L(nt,wetn,rough.inputs[0]);L(nt,rough.outputs[0],b.inputs["Roughness"])
    hgt=math_(nt,'ADD',math_(nt,'MULTIPLY',wv.outputs["Fac"],.6),math_(nt,'MULTIPLY',fn.outputs["Fac"],.4))
    hgt=math_(nt,'SUBTRACT',hgt,math_(nt,'MULTIPLY',crack.outputs[0],.8))
    hgt=math_(nt,'ADD',hgt,nz.outputs["Fac"])
    bp=N(nt,"ShaderNodeBump",Strength=1.0,Distance=.4);L(nt,hgt,bp.inputs["Height"]);L(nt,bp.outputs["Normal"],b.inputs["Normal"])
    return m

STONE=stone_mat("stone",(.20,.185,.16),(.27,.25,.215),(.33,.31,.28))
DSTONE=stone_mat("dstone",(.15,.14,.125),(.2,.19,.17),(.27,.26,.24),scale=1.6)
ROOF=slate_mat("roof")
ROOF_P=slate_mat("roof_pitched",pitched=True)
WIN=mat("win",(1,.5,.15),emit=(1,.45,.12),es=(0.3 if DAY else 10),noise=False)
ROCK=rock_mat("rock")
ROCK2=rock_mat("rock_stack",wscale=.22,wdist=11.0,bdir='DIAGONAL',vscale=.9)

def link(o,m):
    if m is not None: o.data.materials.append(m)
    return o
def cyl(x,y,z0,r,h,m=STONE,v=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=h,location=(x,y,z0+h/2));return link(bpy.context.object,m)
def cone(x,y,z0,r,h,m=ROOF,v=24):
    bpy.ops.mesh.primitive_cone_add(vertices=v,radius1=r,radius2=0,depth=h,location=(x,y,z0+h/2));o=link(bpy.context.object,m);return o
def box(x,y,z,sx,sy,sz,m=STONE,rot=0):
    bpy.ops.mesh.primitive_cube_add(location=(x,y,z),rotation=(0,0,rot));o=bpy.context.object;o.scale=(sx/2,sy/2,sz/2);return link(o,m)

WOOD=mat("wood",(.035,.022,.014),rough=.7,bump=.6)
IRON=mat("iron",(.02,.02,.02),rough=.4,noise=False);IRON.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value=1
GLASS=bpy.data.materials.new("glass");GLASS.use_nodes=True
_nt=GLASS.node_tree;_b=_nt.nodes["Principled BSDF"];_b.inputs["Base Color"].default_value=(.05,.03,.02,1);_b.inputs["Roughness"].default_value=.15
_n=_nt.nodes.new("ShaderNodeTexNoise");_n.inputs["Scale"].default_value=4
_tc=_nt.nodes.new("ShaderNodeTexCoord");_nt.links.new(_tc.outputs["Object"],_n.inputs["Vector"])
_r=_nt.nodes.new("ShaderNodeValToRGB");_r.color_ramp.elements[0].color=(.35,.12,.03,1);_r.color_ramp.elements[1].color=(1,.55,.2,1)
_nt.links.new(_n.outputs["Fac"],_r.inputs[0]);_nt.links.new(_r.outputs[0],_b.inputs["Emission Color"]);_b.inputs["Emission Strength"].default_value=(0.0 if DAY else 1.6);_b.inputs["Roughness"].default_value=.03;_b.inputs["Base Color"].default_value=(.12,.125,.125,1);_b.inputs["Specular IOR Level"].default_value=.8;_b.inputs["Coat Weight"].default_value=0.0
_rn=_nt.nodes.new("ShaderNodeTexVoronoi");_rn.inputs["Scale"].default_value=9;_nt.links.new(_tc.outputs["Object"],_rn.inputs["Vector"])
_rm=_nt.nodes.new("ShaderNodeMapRange");_rm.inputs[3].default_value=.22;_rm.inputs[4].default_value=.28;_nt.links.new(_rn.outputs["Distance"],_rm.inputs[0]);_nt.links.new(_rm.outputs[0],_b.inputs["Roughness"])
# diamond lead grid darkens emission
_w=_nt.nodes.new("ShaderNodeTexWave");_w.wave_profile='SAW';_w.inputs["Scale"].default_value=1
_bk=_nt.nodes.new("ShaderNodeTexChecker")
CUTTERS=[]
def arch_profile(w,h,n=10):
    hs=h-w*0.866
    pts=[(-w/2,0),(w/2,0),(w/2,hs)]
    for i in range(1,n+1):
        a=math.radians(60*i/n);pts.append((-w/2+w*math.cos(a),hs+w*math.sin(a)))
    pts=pts[:-1]+[(0,hs+w*.866)]
    for i in range(n-1,0,-1):
        a=math.radians(60*i/n);pts.append((w/2-w*math.cos(a),hs+w*math.sin(a)))
    pts.append((-w/2,hs))
    return pts
def prism(name,pts,y0,y1,m,loc,rot):
    me=bpy.data.meshes.new(name);bm=bmesh.new()
    f=[bm.verts.new((x,y0,z)) for x,z in pts];b=[bm.verts.new((x,y1,z)) for x,z in pts];n=len(pts)
    bm.faces.new(f);bm.faces.new(list(reversed(b)))
    for i in range(n):
        j=(i+1)%n;bm.faces.new([f[i],f[j],b[j],b[i]])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(0,0,rot)
    if m: o.data.materials.append(m)
    return o
def lbox(par,x,y,z,sx,sy,sz,m):
    bpy.ops.mesh.primitive_cube_add(location=(x,y,z));o=bpy.context.object;o.scale=(sx/2,sy/2,sz/2);link(o,m);o.parent=par;return o
def cut(host,c):
    c.display_type='WIRE';c.hide_render=True;c.visible_camera=False
    md=host.modifiers.new("cut",'BOOLEAN');md.object=c;md.solver='EXACT';host["hasbool"]=1;CUTTERS.append(c)
def gothic_window(x,y,z,w,h,rot,host,depth=.45,tracery=True):
    """real recessed window: outward is local -y; z = sill height"""
    loc=(x,y,z);fr=.14
    root=bpy.data.objects.new("win",None);bpy.context.collection.objects.link(root);root.location=loc;root.rotation_euler=(0,0,rot)
    # stone surround (protrudes 0.12) with opening cut
    frame=prism("frame",arch_profile(w+2*fr,h+fr),-.14,.25,DSTONE,loc,rot)
    hole=prism("hole",arch_profile(w,h),-1,depth+.01,None,loc,rot)
    cut(host,hole);cut(frame,hole)
    # glass at bottom of recess
    g=prism("glass",arch_profile(w,h),depth-.02,depth,GLASS,loc,rot)
    # sill
    s=lbox(root,0,-.1,-.06,w+.45,.55,.14,DSTONE)
    # mullion + transoms + lead bars
    gy=depth-.08
    lbox(root,0,gy,h/2,.07,.08,h*.98,DSTONE)
    for t in (.33,.62):
        lbox(root,0,gy,h*t,w,.07,.06,DSTONE)
    for k in range(1,6):
        lbox(root,0,gy+.03,h*k/7,w,.02,.015,IRON)
    for xx in (-w/4,w/4):
        lbox(root,xx,gy+.03,h*.45,.015,.02,h*.8,IRON)
    if tracery and w>.6:
        # trefoil-ish oculus in the arch head
        bpy.ops.mesh.primitive_torus_add(major_radius=w*.17,minor_radius=.03,location=(0,gy,h-w*.42),rotation=(math.pi/2,0,0))
        o=bpy.context.object;link(o,DSTONE);o.parent=root
    return root
# ---- arrow loops (archères), after Caernarfon / Conwy / Carcassonne types ----
# outer slit ~0.10 m wide, ~1.4 m tall; round oillets at the foot (and head); optional cross arm (balistraria) for crossbows;
# dressed ashlar long-and-short jambs, lintel and sill stone (flush, chamfered); inner embrasure splayed to ~0.9 m -> dark void
ASHLAR=None
_LR=random.Random(1234)   # separate RNG so the main random sequence (window angles etc.) is unchanged
def arrow_loop(host,x,y,zc,a,face,chamber,cross=False,top_oillet=True,H=1.4,W=.10,curv=None):
    global ASHLAR
    if ASHLAR is None:
        # same rough stone shader as the walls, slightly warmer/lighter tone, no procedural brick joints (real joints come from geometry)
        ASHLAR=stone_mat("ashlar",(.235,.218,.19),(.235,.218,.19),(.2,.19,.17))
        for n_ in ASHLAR.node_tree.nodes:
            if n_.type=='TEX_BRICK': n_.inputs["Mortar Size"].default_value=0.0
    ca,sa=math.cos(a),math.sin(a)
    def M(lx,ly,lz): return Vector((x+ca*lx-sa*ly,y+sa*lx+ca*ly,lz))
    bm=bmesh.new()
    from mathutils import Matrix
    R=Matrix.Rotation(a,4,'Z')
    def cube(lx,ly,lz,sx,sy,sz):
        mt=Matrix.Translation(M(lx,ly,lz))@R@Matrix.Diagonal((sx/2,sy/2,sz/2,1))
        bmesh.ops.create_cube(bm,size=2,matrix=mt)
    def disk(lx,lz,r,y0,y1):
        mt=Matrix.Translation(M(lx,(y0+y1)/2,lz))@R@Matrix.Rotation(math.pi/2,4,'X')
        bmesh.ops.create_cone(bm,cap_ends=True,segments=16,radius1=r,radius2=r,depth=y1-y0,matrix=mt)
    yo=face-.35;ys=face+.38          # outer side (local -y is outward) ; slit depth through the outer skin
    cube(0,(yo+ys)/2,zc,W,ys-yo,H)
    # 45-degree chamfer on the outer arrises of the slit (4 cm)
    cv_=[]
    for (lx,ly) in ((-W/2,face+.045),(W/2,face+.045),(W/2+.06,face-.015),(-W/2-.06,face-.015)):
        for lz in (zc-H/2+.02,zc+H/2-.02): cv_.append(bm.verts.new(M(lx,ly,lz)))
    qq=lambda i,j:cv_[i*2+j]
    for f in ((qq(0,0),qq(1,0),qq(2,0),qq(3,0)),(qq(3,1),qq(2,1),qq(1,1),qq(0,1)),(qq(0,0),qq(0,1),qq(1,1),qq(1,0)),(qq(1,0),qq(1,1),qq(2,1),qq(2,0)),(qq(2,0),qq(2,1),qq(3,1),qq(3,0)),(qq(3,0),qq(3,1),qq(0,1),qq(0,0))):
        bm.faces.new(f)
    # splayed embrasure behind the slit (trapezoid in plan), stops inside the wall -> stays dark
    v=[]
    for (lx,ly) in ((-W/2,face+.26),(W/2,face+.26),(.58,chamber),(-.58,chamber)):
        for lz in (zc-H/2-.15,zc+H/2+.15):
            p=M(lx,ly,lz);v.append(bm.verts.new(p))
    q=lambda i,j:v[i*2+j]
    for f in ((q(0,0),q(1,0),q(2,0),q(3,0)),(q(3,1),q(2,1),q(1,1),q(0,1)),(q(0,0),q(0,1),q(1,1),q(1,0)),(q(1,0),q(1,1),q(2,1),q(2,0)),(q(2,0),q(2,1),q(3,1),q(3,0)),(q(3,0),q(3,1),q(0,1),q(0,0))):
        bm.faces.new(f)
    me=bpy.data.meshes.new("loopcut");bm.to_mesh(me);bm.free()
    C=bpy.data.objects.new("loopcut",me);bpy.context.collection.objects.link(C)
    cut(host,C);host.modifiers[-1].use_self=True
    # dressed surround: long-and-short jambs bonded into the 0.3 m wall courses, flush (+4 mm), curved on round towers,
    # same rough stone shader with a slight tone shift; thin joints from 6 mm bevels
    CH=.3
    zb=math.floor((zc-H/2-.05)/CH)*CH;zt=math.ceil((zc+H/2+.05)/CH)*CH
    blocks=[(0,zb-CH,zb,.84)]                       # sill stone, one course
    z=zb;k=0
    while z<zt-1e-6:
        n_=2 if (k%2==0 and z+2*CH<=zt+1e-6) else 1
        ln=(.42 if k%2==0 else .27)+_LR.uniform(-.03,.03)
        for sd in (-1,1): blocks.append((sd*(W/2+ln/2),z,z+n_*CH,ln))
        z+=n_*CH;k+=1
    blocks.append((0,zt,zt+CH,.88))                 # lintel, one course
    for (lx,z0,z1,ln) in blocks:
        bm2=bmesh.new()
        segs=6
        if curv:
            R=curv;phi0=(lx-ln/2)/R;phi1=(lx+ln/2)/R
            ring=[(R*.9985+.003,phi0+(phi1-phi0)*i_/segs) for i_ in range(segs+1)]+[(R-.12,phi1-(phi1-phi0)*i_/segs) for i_ in range(segs+1)]
            P2=[(rr*math.sin(ph),-rr*math.cos(ph)) for rr,ph in ring]
        else:
            P2=[(lx-ln/2+ln*i_/segs,face-.004) for i_ in range(segs+1)]+[(lx+ln/2-ln*i_/segs,face+.12) for i_ in range(segs+1)]
        vb=[bm2.verts.new(M(px_,py_,z0+.002)) for px_,py_ in P2];vt=[bm2.verts.new(M(px_,py_,z1-.002)) for px_,py_ in P2]
        bm2.faces.new(vb[::-1]);bm2.faces.new(vt)
        nP=len(P2)
        for i_ in range(nP):
            j_=(i_+1)%nP;bm2.faces.new([vb[i_],vb[j_],vt[j_],vt[i_]])
        bmesh.ops.recalc_face_normals(bm2,faces=bm2.faces)
        me2=bpy.data.meshes.new("loopstone");bm2.to_mesh(me2);bm2.free()
        o=bpy.data.objects.new("loopstone",me2);bpy.context.collection.objects.link(o);link(o,ASHLAR)
        bv=o.modifiers.new("ch",'BEVEL');bv.width=.006;bv.segments=1
        md=o.modifiers.new("cut",'BOOLEAN');md.object=C;md.solver='EXACT';md.use_self=True
    return C
def gate(x,y,rot,host,w=2.6,h=4.6,depth=1.6):
    loc=(x,y,0)
    root=bpy.data.objects.new("gate",None);bpy.context.collection.objects.link(root);root.location=loc;root.rotation_euler=(0,0,rot)
    hole=prism("gatehole",arch_profile(w,h,14),-2,depth,None,loc,rot);cut(host,hole)
    # voussoirs around arch
    pts=arch_profile(w+.5,h+.25,14);hs=h+.25-(w+.5)*.866
    arc=[p for p in pts if p[1]>=hs-.01 and p!=pts[0] and p!=pts[1]]
    arc.sort(key=lambda p:math.atan2(p[1]-hs,p[0]))
    for i,(px,pz) in enumerate(pts):
        if pz<hs-.01: continue
        nx=pts[(i+1)%len(pts)]
        a=math.atan2(nx[1]-pz,nx[0]-px)
        bpy.ops.mesh.primitive_cube_add(location=(px,-.05,pz))
        o=bpy.context.object;o.scale=(.16,.28,.3);o.rotation_euler=(0,-a,0);link(o,DSTONE if i%2 else STONE);o.parent=root
    bpy.ops.mesh.primitive_cube_add(location=(0,-.08,h+.3));o=bpy.context.object;o.scale=(.25,.32,.4);link(o,DSTONE);o.parent=root  # keystone
    # jamb stones
    for s in (-1,1):
        for k in range(6):
            lbox(root,s*(w/2+.17),-.02,.35+k*.66*(h-w*.87)/4,.34 if k%2 else .46,.4,.6,STONE if k%2 else DSTONE)
    # wooden doors deep inside, with planks and iron straps
    dp=depth-.1
    door=prism("door",arch_profile(w,h,14),dp-.12,dp,WOOD,loc,rot)
    for k in range(9):
        lbox(root,-w/2+w*(k+.5)/9,dp-.13,h*.4,.02,.02,h*.8,DSTONE)
    for zz in (.8,2.2,3.4):
        lbox(root,0,dp-.15,zz,w*.95,.04,.12,IRON)
    # light leaking between doors
    lbox(root,0,dp-.125,h*.45,.03,.01,h*.85,GLASS)
    # portcullis half raised, near front
    for k in range(9):
        lbox(root,-w/2+.1+(w-.2)*k/8,.35,h*.55,.07,.07,h*.7,IRON)
    for k in range(5):
        lbox(root,0,.35,h*.25+h*.12*k,w*.98,.07,.07,IRON)
    for k in range(9):  # spikes
        bpy.ops.mesh.primitive_cone_add(vertices=6,radius1=.06,depth=.25,location=(-w/2+.1+(w-.2)*k/8,.35,h*.2-.1),rotation=(math.pi,0,0));o=bpy.context.object;link(o,IRON);o.parent=root
    # warm torches either side + interior glow
    for s in (-1,1):
        bpy.ops.object.light_add(type='POINT',location=(s*(w/2+.9),-.6,2.6));l=bpy.context.object;l.data.energy=(0 if DAY else 60);l.data.color=(1,.45,.15);l.data.shadow_soft_size=.1;l.parent=root
        lbox(root,s*(w/2+.9),-.45,2.3,.1,.1,.5,IRON)
    bpy.ops.object.light_add(type='POINT',location=(0,dp-.5,1.5));l=bpy.context.object;l.data.energy=(0 if DAY else 40);l.data.color=(1,.5,.2);l.parent=root

TOWERS=[]
def tower(x,y,r,h,spire=2.4,wins=True,crown=True):
    T=cyl(x,y,0,r,h,STONE,40)
    cyl(x,y,h*.98,r*1.18,.6,DSTONE,40)  # machicolation gallery floor (solid, closes the top)
    RT=h*.98+.6
    # corbels
    n=int(14*r)
    for i in range(n):
        a=2*math.pi*i/n;box(x+math.cos(a)*r*1.05,y+math.sin(a)*r*1.05,h*.95,.25,.25,.5,DSTONE,a)
    if crown:
        # parapet wall (breast height ~0.9 m) on the outer edge of the wall-walk deck
        PH=.9;PT=.38;Ro=r*1.18
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=Ro,depth=PH,end_fill_type='NOTHING',location=(x,y,RT+PH/2))
        p=bpy.context.object;sm=p.modifiers.new("s",'SOLIDIFY');sm.thickness=PT;sm.offset=-1;sm.use_even_offset=True;link(p,STONE)
        # merlons on the parapet (sizes per proportions.md)
        mw,mh=(1.1,1.2) if r>=2 else (.75,1.0)
        Rm=Ro-PT/2
        nm=max(6,int(2*math.pi*Rm/(mw+.65)))
        for i in range(nm):
            a=2*math.pi*(i+.5)/nm;box(x+math.cos(a)*Rm,y+math.sin(a)*Rm,RT+PH+mh/2,mw,PT,mh,STONE,a+math.pi/2)
        # roof drum rising from the wall-walk, cone eaves overhang the drum
        DR=r*.8;DH=PH+mh+.3
        cyl(x,y,RT-.05,DR,DH+.05,STONE,40)
        cyl(x,y,RT+DH-.25,DR+.12,.25,DSTONE,40)   # eaves cornice
        CB=RT+DH;CR=DR+.25
    else:
        CB=RT;CR=r*1.24   # cone eaves overhang the machicolation ring
    cone(x,y,CB,CR,2*r*spire)
    TOWERS.append((x,y,r,h,spire,CB,CR))
    # finial
    cyl(x,y,CB+2*r*spire-.1,.04,1.0,DSTONE,8)
    if wins:
        out=math.atan2(y-2,x-1) if (x*x+y*y)>4 else -math.pi/2
        # lower (defensive) level: a single arrow slit; upper (residential) level: one small window
        aa=out+random.uniform(-.5,.5)
        arrow_loop(T,x,y,h*.38+.75,aa+math.pi/2,-r,-r+min(1.0,r*.6),cross=False,curv=r)
        aa=out+random.uniform(-.4,.4)
        w=min(.6,.26*r);gothic_window(x+math.cos(aa)*r,y+math.sin(aa)*r,h*.7,w,w*2.3,aa+math.pi/2,T,depth=.4,tracery=False)
    return T

def wall(p1,p2,h=5,t=1.4):
    p1=Vector(p1);p2=Vector(p2);d=p2-p1;L=d.length;a=math.atan2(d.y,d.x);m=(p1+p2)/2
    W=box(m.x,m.y,h/2,L,t,h,STONE,a)
    for k in range(1,int(L/3.2)):
        q=p1+d*(k/int(L/3.2))
        arrow_loop(W,q.x,q.y,h*.55,a,-t/2,-t/2+1.0)
    box(m.x,m.y,h+.15,L,t+.3,.3,DSTONE,a)
    n=int(L/1.9)
    for i in range(n):
        if True:
            f=(i+.5)/n;q=p1+d*f
            for s in (-1,1):
                off=Vector((-math.sin(a),math.cos(a)))*s*(t/2+.05)
                box(q.x+off.x,q.y+off.y,h+.3+.7,1.2,.4,1.4,STONE,a)

# ---------- ISLAND ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=128,ring_count=64,radius=1,location=(0,0,-6))
isl=bpy.context.object;isl.scale=(34,28,12)
isl.modifiers.new('s0','SUBSURF').levels=1
bpy.ops.object.transform_apply(scale=True)
me=isl.data
for v in me.vertices:
    co=v.co
    if co.z>-6+9: co.z=-6+9+ (co.z-3)*.15  # flatten plateau
    if -3<co.z<3.2:
        f=1+0.075*(((co.z+3)/1.3)%1)-0.025*math.sin(co.z*7.3)+0.015*math.sin(co.z*13)
        co.x*=f;co.y*=f
tx=bpy.data.textures.new("rockn",'VORONOI');tx.noise_scale=6
d=isl.modifiers.new("d",'DISPLACE');d.texture=tx;d.strength=6
tx2=bpy.data.textures.new("rockc",'CLOUDS');tx2.noise_scale=2.5;tx2.noise_depth=4
d2=isl.modifiers.new("d2",'DISPLACE');d2.texture=tx2;d2.strength=5
isl.modifiers.new("s",'SUBSURF').levels=1
tx3=bpy.data.textures.new("rockf",'STUCCI');tx3.noise_scale=.6
d3=isl.modifiers.new("d3",'DISPLACE');d3.texture=tx3;d3.strength=.5;d3.texture_coords='GLOBAL'
link(isl,ROCK);bpy.ops.object.shade_smooth()
STACKS=[];STACKOBJ=[]
txf=bpy.data.textures.new('frac','VORONOI');txf.noise_scale=1.3;txf.distance_metric='CHEBYCHEV';txf.color_mode='INTENSITY'
# scatter crags/sea stacks
for i in range(14):
    a=random.random()*6.28;r=random.uniform(36,55)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4,radius=random.uniform(1.5,4),location=(math.cos(a)*r,math.sin(a)*r,0))
    o=bpy.context.object;o.scale=(random.uniform(.7,1.3),random.uniform(.6,1.2),random.uniform(1.0,2.2));o.rotation_euler=(random.uniform(-.25,.25),random.uniform(-.25,.25),random.random()*6.28);link(o,ROCK2)
    m=o.modifiers.new("d",'DISPLACE');m.texture=tx2;m.strength=2.0;mv=o.modifiers.new('dv','DISPLACE');mv.texture=tx;mv.strength=2.6;mv.texture_coords='GLOBAL';mv2=o.modifiers.new('dv2','DISPLACE');mv2.texture=txf;mv2.strength=1.2;mv2.texture_coords='GLOBAL';o.location.z=-1
    if o.location.y<-25 and abs(o.location.x-3)<22:
        bpy.data.objects.remove(o)
    else:
        STACKS.append((o.location.x,o.location.y,o.dimensions.x/2*1.1));STACKOBJ.append(o);m3=o.modifiers.new('d3','DISPLACE');m3.texture=tx3;m3.strength=.35;m3.texture_coords='GLOBAL';o.modifiers.new('ss','SUBSURF').levels=1

Z=3.6  # plateau height approx
def lift():
    pass
# all castle built at origin then moved up via parent empty
start=set(bpy.data.objects)
# curtain wall (irregular polygon)
pts=[(-16,-12),(10,-14),(18,-2),(14,12),(-6,15),(-18,4)]
for i in range(len(pts)):
    wall(pts[i],pts[(i+1)%len(pts)],h=6)
for (x,y) in pts:
    tower(x,y,2.3,12,spire=1.07)
# gatehouse
GA=math.atan2(-2,26);GH=box(2,-14.5,4,6,3,8,STONE,GA)
gate(2+1.5*math.sin(GA),-14.5-1.5*math.cos(GA),GA,GH)
gothic_window(2+1.5*math.sin(GA),-14.5-1.5*math.cos(GA),5.6,.9,1.9,GA,GH)
tower(-.8,-15.4,1.5,12,1.07);tower(4.8,-16,1.5,12,1.07)
# keep
KP=box(0,2,9,14,10,18,STONE)
box(0,2,18.2,15,11,.5,DSTONE)
for i in range(8):
    for side in (-1,1):
        box(-6.65+i*1.9,2+side*5.6,18.4+.7,1.2,.4,1.4)
        if i<6: box(side*7.3,-2.75+i*1.9,18.4+.7,.4,1.2,1.4)
# keep windows: 2 floors x 4 bays on front, 3 bays on sides
# lower floor (thick defensive wall): two small irregular lights; upper hall floor: large Gothic windows
gothic_window(-3.2,-3,7.2,.55,1.4,0,KP,depth=.5,tracery=False)
gothic_window(3.9,-3,8.1,.55,1.4,0,KP,depth=.5,tracery=False)
for i in range(4):
    gothic_window(-4.5+i*3,-3,12.5,1.05,2.8,0,KP,depth=.5)
for s_ in (-1,1):
    for yy in (0.5,3.5):
        gothic_window(s_*7,yy,12.5,1.0,2.6,(-math.pi/2 if s_>0 else math.pi/2),KP,depth=.5)
# great hall with steep roof + rose window
box(-4,9.5,5,10,6,10)
bpy.ops.mesh.primitive_cube_add(location=(-4,9.5,10));o=bpy.context.object;o.rotation_euler=(0,math.radians(45),0);o.scale=(3.4,3.2,3.4);link(o,ROOF_P)
# keep corner turrets & main spire tower
for (x,y) in [(-7,-3),(7,-3),(-7,7),(7,7)]:
    tower(x,y,1.3,21,spire=1.37,crown=False)
tower(3,4,2.6,30,spire=1.54)   # great spire tower
tower(-3,0,1.6,25,spire=1.54)
# chapel spire
tower(10.5,9.3,1.2,14,spire=1.87,crown=False)
# flying buttress-ish ribs on keep
for i in range(5):
    box(-6+i*3,-3.6,5,.5,1.2,10,DSTONE)
    box(-6+i*3,-3.6,11,.4,.8,4,DSTONE)
# ======== ARCHITECTURAL ENRICHMENT (castle-local coords, lifted with castle) ========
def obox(x,y,z,sx,sy,sz,m=STONE,rx=0,ry=0,rz=0):
    bpy.ops.mesh.primitive_cube_add(location=(x,y,z),rotation=(rx,ry,rz));o=bpy.context.object;o.scale=(sx/2,sy/2,sz/2);return link(o,m)
def gargoyle(x,y,z,a,s=1.0):
    ca,sa=math.cos(a),math.sin(a)
    P=lambda d,h=0,lat=0:(x+ca*d*s-sa*lat*s,y+sa*d*s+ca*lat*s,z+h*s)
    # bonding corbel: tail block runs back into the masonry so the beast is carried by the wall
    obox(*P(.1,-.12),.95*s,.38*s,.32*s,DSTONE,0,0,a)
    bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=.2*s,radius2=.12*s,depth=.8*s,location=P(.45,.05),rotation=(0,math.pi/2-.25,a));o=bpy.context.object;o.scale.x=1.25;link(o,STONE)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.15*s,location=P(.95,.22),segments=12,ring_count=8);o=bpy.context.object;o.scale=(1.35,1,1.05);o.rotation_euler=(0,0,a);link(o,STONE)
    bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.075*s,radius2=.03*s,depth=.32*s,location=P(1.15,.17),rotation=(0,math.pi/2+.2,a));link(bpy.context.object,STONE)  # open-mouthed spout
    for lat in (-1,1):
        bpy.ops.mesh.primitive_cone_add(vertices=6,radius1=.035*s,depth=.22*s,location=P(.9,.4,lat*.08),rotation=(0,-.5,a));link(bpy.context.object,STONE)  # horns
        me=bpy.data.meshes.new("wing");bm=bmesh.new()
        v=[bm.verts.new(p) for p in [P(.35,.15,lat*.12),P(.75,.25,lat*.14),P(.25,.55,lat*.42),P(.1,.35,lat*.3)]]
        bm.faces.new(v);bm.to_mesh(me);bm.free();wo=bpy.data.objects.new("wing",me);bpy.context.collection.objects.link(wo)
        wo.modifiers.new("t",'SOLIDIFY').thickness=.04*s;link(wo,STONE)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.04*s,depth=.25*s,location=P(.7,-.12,lat*.1));link(bpy.context.object,STONE)  # forelegs
def dormer(cx,cy,zb,a,w=.55):
    ca,sa=math.cos(a),math.sin(a)
    obox(cx,cy,zb+w*.55,w*.9,w,w*1.1,STONE,0,0,a+math.pi/2)
    obox(cx+ca*(w*.5+.01),cy+sa*(w*.5+.01),zb+w*.5,w*.5,.04,w*.7,GLASS,0,0,a+math.pi/2)
    bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=w*.78,depth=w*.9,location=(cx,cy,zb+w*1.1+w*.45),rotation=(0,0,a+math.pi/4));link(bpy.context.object,ROOF)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.05,location=(cx,cy,zb+w*2.05),segments=8,ring_count=6);link(bpy.context.object,IRON)

# tower extras: string courses, battered plinths, dormers, gargoyles, finial balls
for (x,y,r,h,sp,CB,CR) in TOWERS:
    for f in (.33,.63):
        cyl(x,y,h*f,r*1.035,.22,DSTONE,40)
    bpy.ops.mesh.primitive_cone_add(vertices=40,radius1=r*1.32,radius2=r*1.01,depth=3.0,location=(x,y,0.0));link(bpy.context.object,STONE)
    cyl(x,y,1.45,r*1.06,.25,DSTONE,40)
    H=2*r*sp;top=CB
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.12,location=(x,y,top+H+.15),segments=12,ring_count=8);link(bpy.context.object,IRON)
    if r>=1.5:
        out=math.atan2(y-2,x-1)
        for j in (-.9,.9):
            a=out+j;t=.22;rr=CR*(1-t)
            dormer(x+math.cos(a)*rr*.92,y+math.sin(a)*rr*.92,top+t*H-.25,a,w=.5*r/2)
        if r>=2.5:   # only the great tower carries gargoyles, two on the sea-facing side
            for a in (-math.pi/2-.55,-math.pi/2+.55):
                gargoyle(x+math.cos(a)*r*1.0,y+math.sin(a)*r*1.0,h*.9,a,s=1.9)
# keep: trim courses, plinth course, flying buttresses with pinnacles
obox(0,2,11.1,14.3,10.3,.3,DSTONE);obox(0,2,1.0,14.5,10.5,.5,DSTONE);obox(0,2,.2,15.2,11.2,1.6,STONE)
obox(0,2,17.6,14.4,10.4,.35,DSTONE)
for i in range(20):  # corbel table under cornice
    obox(-6.8+i*.715,-3.12,17.25,.22,.3,.35,DSTONE)
# ---- Gothic flying buttress system (after Viollet-le-Duc, Dictionnaire, "Arc-boutant"; Amiens/Milan) ----
def flatmesh(name,quads,verts,m,th):
    me=bpy.data.meshes.new(name);bm=bmesh.new();vv=[bm.verts.new(v) for v in verts]
    for q in quads: bm.faces.new([vv[i] for i in q])
    bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    sm=o.modifiers.new("t",'SOLIDIFY');sm.thickness=th;sm.offset=0;link(o,m);return o
def arch_plate(cx,cy,zb,w,H,a,th=.14,n=10):
    """thin face plate with a lancet (equilateral pointed) opening; w=opening width, H=plate top above spring"""
    ca,sa=math.cos(a),math.sin(a);A=w/2+.1
    ins=[];outs=[]
    L=H+A
    for k in range(n+1):
        t=k/n;ang=math.pi-t*(math.pi/3)       # left arc, centre at right spring
        ins.append((w/2+w*math.cos(ang),w*math.sin(ang)))
        s_=t*L;outs.append((-A,s_) if s_<=H else (-A+(s_-H),H))
    I=ins+[(-u,v) for (u,v) in reversed(ins[:-1])];O=outs+[(-u,v) for (u,v) in reversed(outs[:-1])]
    P=lambda u,v:(cx+ca*u,cy+sa*u,zb+v)
    verts=[P(*p) for p in I]+[P(*p) for p in O];N=len(I)
    quads=[(i,i+1,N+i+1,N+i) for i in range(N-1)]
    # jambs below spring
    return flatmesh("arch",quads,verts,STONE,th)
def pinnacle(px,py,z0,sx=1.3,sy=1.1):
    # open aedicule: 4 posts, pointed-arch faces, cap, corner pinnacles, tall crocketed spire, cross
    obox(px,py,z0+.12,sx+.2,sy+.2,.24,DSTONE)
    for ex in (-1,1):
        for ey in (-1,1):
            qx,qy=px+ex*sx/2,py+ey*sy/2
            obox(qx,qy,z0+1.25,.24,.24,2.1,STONE)
            bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=.17,depth=1.1,location=(qx,qy,z0+2.95),rotation=(0,0,math.pi/4));link(bpy.context.object,STONE)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=.06,location=(qx,qy,z0+3.52),segments=8,ring_count=5);link(bpy.context.object,STONE)
    obox(px,py,z0+.9,.32,.32,1.6,STONE)   # central shaft seen through arches
    for (fx,fy,aa,ww) in ((0,-sy/2,0,sx-.3),(0,sy/2,0,sx-.3),(-sx/2,0,math.pi/2,sy-.3),(sx/2,0,math.pi/2,sy-.3)):
        arch_plate(px+fx,py+fy,z0+1.1,ww,1.05,aa)
    obox(px,py,z0+2.3,sx+.12,sy+.12,.22,DSTONE)
    # spire 4.5 m
    bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=.62,depth=4.5,location=(px,py,z0+2.41+2.25),rotation=(0,0,math.pi/4));link(bpy.context.object,STONE)
    for k in range(5):            # crockets: small wedges on each arris
        zz=z0+2.9+k*.78;r_=.62*(1-(zz-(z0+2.41))/4.5)
        for q in range(4):
            aq=q*math.pi/2+math.pi/4
            bpy.ops.mesh.primitive_cone_add(vertices=3,radius1=.1,depth=.26,location=(px+math.cos(aq)*(r_*.72+.05),py+math.sin(aq)*(r_*.72+.05),zz),rotation=(math.pi/2-.6,0,aq+math.pi/2));link(bpy.context.object,STONE)
    obox(px,py,z0+7.15,.07,.07,.7,STONE);obox(px,py,z0+7.25,.38,.07,.07,STONE)   # finial cross
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.1,location=(px,py,z0+6.85),segments=8,ring_count=6);link(bpy.context.object,STONE)
def prism(name,prof,y0,y1,m,bev=.02):
    me=bpy.data.meshes.new(name);bm=bmesh.new();n_=len(prof)
    fv=[bm.verts.new((x_,y0,z_)) for x_,z_ in prof];bv=[bm.verts.new((x_,y1,z_)) for x_,z_ in prof]
    bm.faces.new(fv);bm.faces.new(list(reversed(bv)))
    for i_ in range(n_):
        j_=(i_+1)%n_;bm.faces.new([fv[i_],fv[j_],bv[j_],bv[i_]])
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);link(o,m)
    if bev: o.modifiers.new("b",'BEVEL').width=bev
    return o
def flyer(s_,yy,xw,xp,zc,zw_top,zp_top,w=.95,ring=.65,nv=11):
    """scimitar flyer: voussoir arch ring on a quarter-circle intrados (centre (xw,zc), R=span; vertical at pier, horizontal at wall),
       solid spandrel up to a straight sloped extrados, V coping with water channel"""
    R=abs(xp-xw);xe=xw-s_*.45
    C=lambda r,th:(xw+s_*r*math.cos(th),zc+r*math.sin(th))
    # spandrel/core (slightly narrower, darker joints show between voussoirs)
    arcO=[C(R+ring-.04,k/24*math.pi/2) for k in range(25)]
    prof=[(xp,zp_top),(xw,zw_top),(xe,zw_top),(xe,zc+R+ring-.04)]+list(reversed(arcO))
    prism("flyer_spandrel",prof,yy-w/2+.06,yy+w/2-.06,STONE)
    arcI=[C(R+.02,k/24*math.pi/2) for k in range(25)]
    prism("flyer_core",[(xp,zc)]+arcO[::-1][::-1]+[(xw,zc+R+.02)]+arcI[::-1],yy-w/2+.08,yy+w/2-.08,DSTONE,0)
    # voussoirs: radial joints
    for k in range(nv):
        t0=k/nv*math.pi/2+.012;t1=(k+1)/nv*math.pi/2-.012
        pts=[C(R,t0+(t1-t0)*q/3) for q in range(4)]+[C(R+ring,t1-(t1-t0)*q/3) for q in range(4)]
        prism("voussoir",pts,yy-w/2,yy+w/2,STONE,.025)
    # coping: shallow V of two slabs + dark channel, slightly wider than the flyer
    Lf=math.hypot(xw-xp,zw_top-zp_top)+.3;ang=math.atan2(zw_top-zp_top,abs(xw-xp))
    mx,mz=(xp+xw)/2,(zp_top+zw_top)/2
    for side in (-1,1):
        obox(mx,yy+side*.29,mz+.1,Lf,.52,.2,DSTONE,-side*.12,s_*ang,0)
    obox(mx,yy,mz+.07,Lf,.16,.06,ROOF,0,s_*ang,0)
XW=7.0;XP=12.0      # wall face / pier inner face (5 m clear)
for s_ in (-1,1):
    for yy in (-1.0,2.0,5.0):
        xi=s_*XP
        # pier: 3 setback stages on the outer face, sloped weatherings + moulding courses
        stages=((0,6.0,2.4,1.3),(6.0,11.0,2.1,1.15),(11.0,17.4,1.8,1.0))
        obox(s_*(XP+1.3),yy,-1.5,3.0,1.8,3.6,STONE)                        # footing into the rock
        obox(s_*(XP+1.3),yy,.45,2.8,1.7,.9,DSTONE)                         # base plinth
        obox(s_*(XP+1.25),yy,1.05,2.6,1.5,.2,DSTONE)
        for (z0_,z1_,dp,wd) in stages:
            obox(s_*(XP+dp/2),yy,(z0_+z1_)/2,dp,wd,z1_-z0_,STONE)
            if z1_<17:
                obox(s_*(XP+dp-.32),yy,z1_+.05,.9,wd+.04,.32,DSTONE,0,s_*.62,0)   # weathering
                obox(s_*(XP+dp/2+.04),yy,z1_-.22,dp+.12,wd+.12,.16,DSTONE)      # moulding course
        obox(s_*(XP+.9),yy,17.45,2.0,1.2,.22,DSTONE)                             # cornice to pinnacle
        pinnacle(s_*(XP+.9),yy,17.56,1.3,.9)
        # two tiers of flyers
        flyer(s_,yy,s_*XW,xi,11.8,17.9,16.2)     # upper, under the eave
        flyer(s_,yy,s_*XW,xi,5.0,11.2,9.4)      # lower, at clerestory-sill level
        # wall responds: colonnettes with capitals and shafts receiving each flyer head
        obox(s_*(XW+.17),yy,8.8,.5,1.1,17.6,STONE)                               # wall pilaster/respond bonded to the wall
        obox(s_*(XW+.25),yy,.6,.75,1.4,1.2,DSTONE)                              # respond base moulding
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.2,depth=15.6,location=(s_*(XW+.42),yy,8.4));link(bpy.context.object,STONE)
        for zc_ in (10.0,16.8):
            obox(s_*(XW+.4),yy,zc_-.1,.7,.85,.35,DSTONE)
            bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=.2,radius2=.34,depth=.4,location=(s_*(XW+.42),yy,zc_-.45));link(bpy.context.object,DSTONE)
        # gargoyle at the foot of the upper channel, projecting outward from the pier
        gargoyle(s_*(XP+1.8),yy,15.8,0 if s_>0 else math.pi,1.15)
# great hall: ridge, finials, chimneys, quoins
obox(-4,9.5,14.75,.3,6.9,.3,DSTONE)
for yy in (6.2,12.8):
    bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.18,depth=.9,location=(-4,yy,15.3));link(bpy.context.object,IRON)
for (cx,cy) in ((-7,8),(-1.2,11.6)):
    obox(cx,cy,12.5,.9,.9,6,STONE);obox(cx,cy,15.6,1.1,1.1,.25,DSTONE)
    for dx in (-.25,.25): obox(cx+dx,cy,15.9,.25,.25,.4,DSTONE)
for (qx,qy) in ((-9,6.5),(1,6.5),(-9,12.5),(1,12.5)):
    for k in range(12):
        big=k%2==0
        obox(qx+(.25 if qx>0 else -.25)*(0 if big else 1),qy+(.25 if qy>9 else -.25)*(1 if big else 0),.4+k*.82,.9 if big else .55,.55 if big else .9,.78,DSTONE)
# chapel buttresses
for k in range(4):
    a=k*math.pi/2+math.pi/4
    obox(10.5+math.cos(a)*1.45,9.3+math.sin(a)*1.45,4,.5,.5,8,STONE,0,0,a)
    bpy.ops.mesh.primitive_cone_add(vertices=4,radius1=.35,depth=1.4,location=(10.5+math.cos(a)*1.45,9.3+math.sin(a)*1.45,8.7));link(bpy.context.object,STONE)
# curtain wall: battered plinth
for i in range(len(pts)):
    p1=Vector(pts[i]);p2=Vector(pts[(i+1)%len(pts)]);d=p2-p1;a=math.atan2(d.y,d.x);m=(p1+p2)/2
    obox(m.x,m.y,-.3,d.length,2.6,2.4,STONE,0,0,a);obox(m.x,m.y,.95,d.length,1.75,.3,DSTONE,0,0,a)

castle=[o for o in bpy.data.objects if o not in start]
for o in castle:
    o.location.z+=Z;o.location.x+=1;o.location.y+=0
    if o.type=='MESH' and "hasbool" not in o and o.parent is None and o not in CUTTERS: o.modifiers.new("b",'BEVEL').width=.04
    if o.parent is not None: o.location.z-=Z;o.location.x-=1

# ---------- OCEAN ----------
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,0))
oc=bpy.context.object
om=oc.modifiers.new("ocean",'OCEAN');om.geometry_mode='GENERATE';om.repeat_x=om.repeat_y=7
om.size=10;om.spatial_size=150;om.resolution=16;om.wave_scale=12.0;om.choppiness=3.0;om.wind_velocity=28
om.use_foam=True;om.foam_layer_name="foam";om.foam_coverage=.25
oc.scale=(1,1,1)
# tile ocean via array
oc.location=(-525,-525,0)
_dg=bpy.context.evaluated_depsgraph_get()
_S=[]
for (sx,sy,_r),so_ in zip(STACKS,STACKOBJ):
    ev=so_.evaluated_get(_dg);mw=so_.matrix_world
    ds=[((mw@v.co).xy-Vector((sx,sy))).length for v in ev.data.vertices if abs((mw@v.co).z)<.5]
    _S.append((sx,sy,(sorted(ds)[len(ds)//2] if ds else _r)))
STACKS=_S
om_m=bpy.data.materials.new("sea");om_m.use_nodes=True;nt=om_m.node_tree;b=nt.nodes["Principled BSDF"]
WATER=(.004,.035,.045,1) if DAY else (.005,.015,.022,1)
b.inputs["Roughness"].default_value=.08;b.inputs["IOR"].default_value=1.33
b.inputs["Subsurface Weight"].default_value=0
geo=N(nt,"ShaderNodeNewGeometry");pos=geo.outputs["Position"];sep=N(nt,"ShaderNodeSeparateXYZ");L(nt,pos,sep.inputs[0])
ex=math_(nt,'DIVIDE',sep.outputs["X"],27.0);ey=math_(nt,'DIVIDE',sep.outputs["Y"],22.5)
cxy=N(nt,"ShaderNodeCombineXYZ");L(nt,ex,cxy.inputs[0]);L(nt,ey,cxy.inputs[1])
ln=N(nt,"ShaderNodeVectorMath",operation='LENGTH');L(nt,cxy.outputs[0],ln.inputs[0])
D=math_(nt,'MULTIPLY',math_(nt,'SUBTRACT',ln.outputs["Value"],1.0),27.0)
for (x,y,r) in STACKS:
    dx=math_(nt,'SUBTRACT',sep.outputs["X"],x);dy=math_(nt,'SUBTRACT',sep.outputs["Y"],y)
    c2=N(nt,"ShaderNodeCombineXYZ");L(nt,dx,c2.inputs[0]);L(nt,dy,c2.inputs[1])
    l2=N(nt,"ShaderNodeVectorMath",operation='LENGTH');L(nt,c2.outputs[0],l2.inputs[0])
    D=math_(nt,'MINIMUM',D,math_(nt,'SUBTRACT',l2.outputs["Value"],r))
wn=N(nt,"ShaderNodeTexNoise",Scale=.2,Detail=4.0);L(nt,pos,wn.inputs["Vector"])
D=math_(nt,'ADD',D,math_(nt,'MULTIPLY',math_(nt,'SUBTRACT',wn.outputs["Fac"],.5),6.0))
near=N(nt,"ShaderNodeMapRange");near.inputs[1].default_value=-1.5;near.inputs[2].default_value=3.0;near.inputs[3].default_value=1;near.inputs[4].default_value=0;L(nt,D,near.inputs[0])
# streaky fbm foam (stretched noise, distorted) -- no cellular pattern
mp=N(nt,"ShaderNodeMapping");mp.inputs["Scale"].default_value=(.7,1.6,1);L(nt,pos,mp.inputs[0])
fn=N(nt,"ShaderNodeTexNoise",Scale=1.4,Detail=14.0,Roughness=.72,Distortion=1.5);L(nt,mp.outputs[0],fn.inputs["Vector"])
fine=N(nt,"ShaderNodeTexNoise",Scale=9.0,Detail=8.0,Roughness=.7);L(nt,pos,fine.inputs["Vector"])
fb=math_(nt,'MULTIPLY',fn.outputs["Fac"],math_(nt,'ADD',fine.outputs["Fac"],.5))
# threshold falls as we approach rock: dense near rock, scattered outward
thr=N(nt,"ShaderNodeMapRange");thr.inputs[3].default_value=.95;thr.inputs[4].default_value=.5;L(nt,near.outputs[0],thr.inputs[0])
sh=math_(nt,'MULTIPLY',math_(nt,'SUBTRACT',fb,thr.outputs[0]),8.0)
sh=math_(nt,'MULTIPLY',math_(nt,'MINIMUM',math_(nt,'MAXIMUM',sh,0.0),1.0),math_(nt,'GREATER_THAN',near.outputs[0],.75))
# whitecaps: ocean foam attribute broken by fine noise
at=nt.nodes.new("ShaderNodeAttribute");at.attribute_name="foam"
wc_=math_(nt,'MULTIPLY',math_(nt,'SUBTRACT',math_(nt,'MULTIPLY',at.outputs["Fac"],fine.outputs["Fac"]),.75),3.0)
wc_=math_(nt,'MINIMUM',math_(nt,'MAXIMUM',wc_,0.0),.85)
# lacy filaments: ridged noise -> thin connected lines, only within ~4 m of rock
rg=N(nt,"ShaderNodeTexNoise",Scale=2.2,Detail=6.0,Roughness=.55,Distortion=2.0);L(nt,mp.outputs[0],rg.inputs["Vector"])
ridge=math_(nt,'SUBTRACT',1.0,math_(nt,'MULTIPLY',math_(nt,'ABSOLUTE',math_(nt,'SUBTRACT',rg.outputs["Fac"],.5)),14.0))
ridge=math_(nt,'MAXIMUM',ridge,0.0)
lace_=math_(nt,'MULTIPLY',math_(nt,'MULTIPLY',ridge,near.outputs[0]),math_(nt,'ADD',fine.outputs["Fac"],.3))
cf_=math_(nt,'MINIMUM',lace_,.85)
f=math_(nt,'MAXIMUM',math_(nt,'MAXIMUM',sh,wc_),cf_)
# water body colour: deep blue-green, lighter shallow near rocks, plus wave-height tint
hz=N(nt,"ShaderNodeMapRange");hz.inputs[1].default_value=-1.5;hz.inputs[2].default_value=2.0;L(nt,sep.outputs["Z"],hz.inputs[0])
wcol=mixc(nt,math_(nt,'MULTIPLY',hz.outputs[0],.5),WATER,(.02,.09,.1,1))
wcol=mixc(nt,math_(nt,'MULTIPLY',near.outputs[0],.7),wcol,(.04,.13,.12,1))
col=mixc(nt,f,wcol,(.85,.88,.9,1))
L(nt,col,b.inputs["Base Color"])
rr=N(nt,"ShaderNodeMapRange");rr.inputs[3].default_value=.09;rr.inputs[4].default_value=.8;L(nt,f,rr.inputs[0]);L(nt,rr.outputs[0],b.inputs["Roughness"])
# small capillary ripples to break mirror tiling
rn=N(nt,"ShaderNodeTexNoise",Scale=1.2,Detail=10.0,Roughness=.6);L(nt,pos,rn.inputs["Vector"])
wmp=N(nt,"ShaderNodeMapping");wmp.inputs["Scale"].default_value=(.35,1.0,1);wmp.inputs["Rotation"].default_value=(0,0,.5);L(nt,pos,wmp.inputs[0])
ww=N(nt,"ShaderNodeTexWave",wave_type='BANDS',bands_direction='X');ww.inputs["Scale"].default_value=.08;ww.inputs["Distortion"].default_value=14;ww.inputs["Detail"].default_value=8;L(nt,wmp.outputs[0],ww.inputs["Vector"])
wh=math_(nt,'ADD',math_(nt,'MULTIPLY',ww.outputs["Fac"],.7),math_(nt,'ADD',rn.outputs["Fac"],f))
bp=N(nt,"ShaderNodeBump",Strength=.85,Distance=.35);L(nt,wh,bp.inputs["Height"]);L(nt,bp.outputs["Normal"],b.inputs["Normal"])
oc.data.materials.append(om_m);bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_plane_add(size=40000,location=(0,0,-.15));fp=bpy.context.object;fp.name="FarSea";fp.data.materials.append(om_m)

# ---------- SPLASH: crown-shaped spray sheets + droplets where waves hit rock ----------
dg=bpy.context.evaluated_depsgraph_get()
SPR=bpy.data.materials.new("splash");SPR.use_nodes=True;nt=SPR.node_tree;nt.nodes.clear()
o_=N(nt,"ShaderNodeOutputMaterial");tr=N(nt,"ShaderNodeBsdfTransparent");pb=N(nt,"ShaderNodeBsdfPrincipled")
pb.inputs["Base Color"].default_value=(.9,.93,.95,1);pb.inputs["Roughness"].default_value=.5;pb.inputs["Subsurface Weight"].default_value=.5
uv=N(nt,"ShaderNodeUVMap");sp_=N(nt,"ShaderNodeSeparateXYZ");L(nt,uv.outputs[0],sp_.inputs[0])
mpp=N(nt,"ShaderNodeMapping");mpp.inputs["Scale"].default_value=(6,1.2,1);L(nt,uv.outputs[0],mpp.inputs[0])
sn_=N(nt,"ShaderNodeTexNoise",Scale=3.0,Detail=12.0,Roughness=.7,Distortion=.8);L(nt,mpp.outputs[0],sn_.inputs["Vector"])
fade=N(nt,"ShaderNodeMapRange");fade.inputs[1].default_value=.15;fade.inputs[2].default_value=1;fade.inputs[3].default_value=1;fade.inputs[4].default_value=0;L(nt,sp_.outputs["Y"],fade.inputs[0])
edge=math_(nt,'SINE',math_(nt,'MULTIPLY',sp_.outputs["X"],math.pi))
a_=math_(nt,'MULTIPLY',math_(nt,'MULTIPLY',fade.outputs[0],edge),sn_.outputs["Fac"])
a_=N(nt,"ShaderNodeMapRange");L(nt,math_(nt,'MULTIPLY',math_(nt,'MULTIPLY',fade.outputs[0],edge),sn_.outputs["Fac"]),a_.inputs[0]);a_.inputs[1].default_value=.18;a_.inputs[2].default_value=.4
ms=N(nt,"ShaderNodeMixShader");L(nt,a_.outputs[0],ms.inputs[0]);L(nt,tr.outputs[0],ms.inputs[1]);L(nt,pb.outputs[0],ms.inputs[2]);L(nt,ms.outputs[0],o_.inputs[0])
SPRAY=bpy.data.materials.new("drops");SPRAY.use_nodes=True;sb=SPRAY.node_tree.nodes["Principled BSDF"]
sb.inputs["Base Color"].default_value=(.9,.92,.93,1);sb.inputs["Roughness"].default_value=.35;sb.inputs["Transmission Weight"].default_value=.5
from mathutils import Matrix
dbm=bmesh.new();sbm=bmesh.new();uvl=sbm.loops.layers.uv.new()
def sheet(p,nrm,width,height):
    tang=Vector((-nrm.y,nrm.x,0));nu,nv=10,6;vs=[]
    for j in range(nv+1):
        row=[];t=j/nv
        for i in range(nu+1):
            s=i/nu-.5
            out=nrm*(t*t*height*.9+ .3)+tang*s*width*(1+t*.8)
            q=p+out+Vector((0,0,t*height*(1-abs(s)*.8)+random.uniform(-.1,.1)))
            row.append(sbm.verts.new(q))
        vs.append(row)
    for j in range(nv):
        for i in range(nu):
            f=sbm.faces.new([vs[j][i],vs[j][i+1],vs[j+1][i+1],vs[j+1][i]])
            for l,(a,bq) in zip(f.loops,[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]): l[uvl].uv=(a/nu,bq/nv)
def drops(p,nrm,n,height):
    for i in range(n):
        t=random.random()**1.5
        q=p+nrm*(t*3.5+.3)+Vector((-nrm.y,nrm.x,0))*random.gauss(0,1.0)+Vector((0,0,height*random.random()**.7*(1.2-t*.6)))
        bmesh.ops.create_icosphere(dbm,subdivisions=1,radius=random.uniform(.015,.05),matrix=Matrix.Translation(q))
targets=[(0,0,40)]+[(x,y,r+6) for x,y,r in STACKS]
for (cx,cy,R) in targets:
    na=40 if R==40 else 5
    for k in range(na):
        a=2*math.pi*(k+random.random()*.5)/na
        org=Vector((cx+math.cos(a)*R*1.4,cy+math.sin(a)*R*1.4,.4))
        hit,loc,nrm,idx,ob,mtx=sc.ray_cast(dg,org,(Vector((cx,cy,.4))-org).normalized())
        if hit and ob is not None and ob.name.startswith(("Sphere","Icosphere")) and random.random()<.7:
            n2=Vector((nrm.x,nrm.y,0)).normalized();h=random.uniform(1.0,2.6) if R==40 else random.uniform(.8,1.6)
            sheet(loc-n2*.3+Vector((0,0,-.3)),n2,random.uniform(1.8,3.5),h)
            drops(loc,n2,random.randint(150,350),h*1.1)
for nm,bmx,mt_ in (("Splash",sbm,SPR),("Drops",dbm,SPRAY)):
    me=bpy.data.meshes.new(nm);bmx.to_mesh(me);bmx.free();o=bpy.data.objects.new(nm,me);bpy.context.collection.objects.link(o);me.materials.append(mt_);o.visible_shadow=False

# ======== WORLD-SPACE EXTRAS: stair path + landing, rubble talus ========
GX,GY=2.88,-16.2
nst=20
for i in range(nst):
    zt=ZW-(i+1)*(ZW-.7)/nst;yy=GY-1.0-i*.55
    obox(GX,yy,(zt-1.5)/2,3.0,.58,zt+1.5,STONE)
    obox(GX,yy-.25,zt-.02,3.05,.1,.06,DSTONE)
for s_ in (-1,1):
    y0,y1=GY-3.2,GY-1.0-nst*.55;z0,z1=ZW-1.3+.5,.7+.5
    Lp=math.hypot(y1-y0,z1-z0);ang=math.atan2(z1-z0,y1-y0)
    obox(GX+s_*1.7,(y0+y1)/2,(z0+z1)/2,.45,Lp,.9,STONE,ang,0,0)
    obox(GX+s_*1.7,(y0+y1)/2,(z0+z1)/2+.5,.6,Lp,.15,DSTONE,ang,0,0)
# landing / sea gate jetty
LY=GY-1.0-nst*.55-3.0
obox(GX,LY,-.6,5,6,2.6,STONE);obox(GX,LY,.75,5.3,6.3,.2,DSTONE)
for k in range(5):  # supporting arches under the jetty
    obox(GX-2.3+k*1.15,LY-3.05,-.4,.5,.3,2.2,DSTONE)
for (bx,by) in ((-2,-2.6),(2,-2.6),(-2,2.2),(2,2.2)):
    cyl(GX+bx,LY+by,.85,.18,.7,IRON,10)
# rubble / talus: drop stones on to the real island surface along castle footprint
dg=bpy.context.evaluated_depsgraph_get()
from mathutils import Matrix
rb=bmesh.new();ab=bmesh.new()
foot=[(p[0]+1,p[1]) for p in pts]
for i in range(len(foot)):
    p1=Vector(foot[i]);p2=Vector(foot[(i+1)%len(foot)]);d=p2-p1
    nrm=Vector((d.y,-d.x)).normalized()
    if (((p1+p2)/2)).dot(nrm)<0: nrm=-nrm
    for k in range(90):
        f=random.random();off=random.random()**1.6*7+1.0
        q=p1+d*f+nrm*off
        hit,loc,n,idx,ob,mx=sc.ray_cast(dg,Vector((q.x,q.y,30)),Vector((0,0,-1)))
        if not hit or ob is None or not ob.name.startswith("Sphere"): continue
        s=random.uniform(.12,.55)*(1.4 if off<2.5 else 1)
        M=Matrix.Translation(loc)@Matrix.Rotation(random.random()*6.28,4,'Z')@Matrix.Diagonal((s*random.uniform(.8,1.5),s,s*random.uniform(.5,.9),1))
        if random.random()<.25:
            bmesh.ops.create_cube(ab,size=1.4,matrix=M@Matrix.Rotation(random.uniform(-.5,.5),4,'X'))
        else:
            bmesh.ops.create_icosphere(rb,subdivisions=1,radius=1,matrix=M)
for nm,bmx,mt_ in (("Talus",rb,ROCK2),("Ashlar",ab,STONE)):
    me=bpy.data.meshes.new(nm);bmx.to_mesh(me);bmx.free();o=bpy.data.objects.new(nm,me);bpy.context.collection.objects.link(o);me.materials.append(mt_)
    if nm=="Talus": md=o.modifiers.new("d",'DISPLACE');md.texture=tx;md.strength=.15;md.texture_coords='GLOBAL'
    else: o.modifiers.new("b",'BEVEL').width=.05
# surf mist: low ring of thin volumetric spray around the shore
mist=bpy.data.materials.new("mist");mist.use_nodes=True;nt=mist.node_tree;nt.nodes.remove(nt.nodes["Principled BSDF"])
tc=N(nt,"ShaderNodeTexCoord");sp=N(nt,"ShaderNodeSeparateXYZ");L(nt,tc.outputs["Object"],sp.inputs[0])
cx_=N(nt,"ShaderNodeCombineXYZ");L(nt,sp.outputs["X"],cx_.inputs[0]);L(nt,sp.outputs["Y"],cx_.inputs[1])
ln=N(nt,"ShaderNodeVectorMath",operation='LENGTH');L(nt,cx_.outputs[0],ln.inputs[0])
ring=math_(nt,'SUBTRACT',1.0,math_(nt,'MULTIPLY',math_(nt,'ABSOLUTE',math_(nt,'SUBTRACT',ln.outputs["Value"],.52)),12.0))
ring=math_(nt,'MAXIMUM',ring,0.0)
hf=math_(nt,'POWER',math_(nt,'MAXIMUM',math_(nt,'SUBTRACT',1.0,math_(nt,'MULTIPLY',math_(nt,'ADD',sp.outputs["Z"],1.0),.5)),0.0),2.0)
nz=N(nt,"ShaderNodeTexNoise",Scale=6.0,Detail=6.0);L(nt,tc.outputs["Object"],nz.inputs["Vector"])
nm_=N(nt,"ShaderNodeMapRange");nm_.inputs[1].default_value=.45;nm_.inputs[2].default_value=.75;L(nt,nz.outputs["Fac"],nm_.inputs[0])
dens=math_(nt,'MULTIPLY',math_(nt,'MULTIPLY',ring,hf),math_(nt,'MULTIPLY',nm_.outputs[0],.008))
vp=N(nt,"ShaderNodeVolumePrincipled");vp.inputs["Color"].default_value=(.92,.94,.96,1);L(nt,dens,vp.inputs["Density"])
L(nt,vp.outputs[0],nt.nodes["Material Output"].inputs["Volume"])
bpy.ops.mesh.primitive_cube_add(location=(0,0,2.0));mo_=bpy.context.object;mo_.name="SurfMist";mo_.scale=(58,48,2.6);mo_.data.materials.append(mist)
mo_.visible_shadow=False

# ---------- BATS ----------
bpy.ops.mesh.primitive_plane_add(size=1);bat=bpy.context.object
bm=bmesh.new();vs=[bm.verts.new(p) for p in [(0,0,0),(-.6,.25,.12),(-1,-.05,.25),(-.5,-.15,.05),(.5,-.15,.05),(1,-.05,.25),(.6,.25,.12)]]
bm.faces.new([vs[0],vs[1],vs[2],vs[3]]);bm.faces.new([vs[0],vs[4],vs[5],vs[6]])
bm.to_mesh(bat.data);bm.free()
bpy.data.meshes.remove(bpy.data.meshes[0]) if False else None
bm_=bpy.data.materials.new("bat");bm_.diffuse_color=(0,0,0,1);bm_.use_nodes=True;bm_.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0,0,0,1)
bat.data.materials.append(bm_);bat.location=(0,0,-100)
for i in range(0 if DAY else 28):
    o=bat.copy();bpy.context.collection.objects.link(o)
    a=random.uniform(-.6,1.6);r=random.uniform(8,30)
    o.location=(4+math.cos(a)*r,-math.sin(a)*r*.6-6,random.uniform(28,52));s=random.uniform(.5,1.1);o.scale=(s,s,s)
    o.rotation_euler=(random.uniform(-.4,.4),random.uniform(-.4,.4),random.uniform(0,6.28))

def setup_night():
    # ---------- WORLD / LIGHT ----------
    w=bpy.data.worlds.new("w");sc.world=w;w.use_nodes=True;nt=w.node_tree
    bg=nt.nodes["Background"];sky=nt.nodes.new("ShaderNodeTexGradient")
    tc=nt.nodes.new("ShaderNodeTexCoord");sep=nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"],sep.inputs[0])
    cr=nt.nodes.new("ShaderNodeValToRGB");cr.color_ramp.elements[0].position=.5;cr.color_ramp.elements[0].color=(.06,.03,.07,1)
    cr.color_ramp.elements[1].position=.75;cr.color_ramp.elements[1].color=(.004,.008,.025,1)
    e=cr.color_ramp.elements.new(.56);e.color=(.03,.03,.06,1)
    # map z (-1..1) ->0..1
    mt=nt.nodes.new("ShaderNodeMapRange");mt.inputs[1].default_value=-1;mt.inputs[2].default_value=1
    nt.links.new(sep.outputs["Z"],mt.inputs[0]);nt.links.new(mt.outputs[0],cr.inputs[0])
    # clouds
    nz=nt.nodes.new("ShaderNodeTexNoise");nz.inputs["Scale"].default_value=3;nz.inputs["Detail"].default_value=10
    cr2=nt.nodes.new("ShaderNodeValToRGB");cr2.color_ramp.elements[0].position=.45;cr2.color_ramp.elements[1].position=.75
    nt.links.new(tc.outputs["Generated"],nz.inputs["Vector"]);nt.links.new(nz.outputs["Fac"],cr2.inputs[0])
    mx=nt.nodes.new("ShaderNodeMix");mx.data_type='RGBA';mx.inputs["B"].default_value=(.07,.075,.1,1)
    nt.links.new(cr.outputs["Color"],mx.inputs["A"]);nt.links.new(cr2.outputs["Color"],mx.inputs["Factor"])
    nt.links.new(mx.outputs["Result"],bg.inputs["Color"]);bg.inputs["Strength"].default_value=1.0
    # world fog
    vs_=nt.nodes.new("ShaderNodeVolumePrincipled");vs_.inputs["Density"].default_value=.0035;vs_.inputs["Color"].default_value=(.6,.65,.8,1)
    nt.links.new(vs_.outputs[0],nt.nodes["World Output"].inputs["Volume"])
    
    # moon: emissive sphere far away + moonlight sun
    MOON=(-60,330,105)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=20,location=MOON,segments=64,ring_count=32)
    mo=bpy.context.object;mm=bpy.data.materials.new("moon");mm.use_nodes=True;n2=mm.node_tree
    em=n2.nodes.new("ShaderNodeEmission");nz=n2.nodes.new("ShaderNodeTexNoise");nz.inputs["Scale"].default_value=2.5;nz.inputs["Detail"].default_value=6
    r=n2.nodes.new("ShaderNodeValToRGB");r.color_ramp.elements[0].color=(.55,.55,.5,1);r.color_ramp.elements[1].color=(1,.97,.85,1)
    n2.links.new(nz.outputs["Fac"],r.inputs[0]);n2.links.new(r.outputs[0],em.inputs[0]);em.inputs[1].default_value=12
    n2.links.new(em.outputs[0],n2.nodes["Material Output"].inputs[0]);n2.nodes.remove(n2.nodes["Principled BSDF"])
    mo.data.materials.append(mm);mo.visible_volume_scatter=False
    mo.visible_shadow=False
    bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.6;sun.data.color=(.55,.65,1);sun.data.angle=.02
    sun.rotation_euler=(Vector(MOON)*-1).to_track_quat('-Z','Y').to_euler()
    # warm interior point lights
    for p in [(1,-.5,12),(-4,9,8),(3,4,25),(2,-14,6),(-3,0,20)]:
        bpy.ops.object.light_add(type='POINT',location=(p[0]+1,p[1]-4,p[2]+Z));l=bpy.context.object;l.data.energy=600;l.data.color=(1,.5,.2);l.data.shadow_soft_size=1.5
    bpy.ops.object.light_add(type='AREA',location=(40,-110,45));l=bpy.context.object;l.data.energy=45000;l.data.size=60;l.data.color=(.45,.55,.9);l.visible_volume_scatter=False
    l.rotation_euler=(Vector((0,0,4))-l.location).to_track_quat('-Z','Y').to_euler()
    # rim light from behind
    bpy.ops.object.light_add(type='AREA',location=(10,60,40));l=bpy.context.object;l.data.energy=40000;l.data.size=40;l.data.color=(.5,.6,1)
    l.rotation_euler=(Vector((0,0,15))-l.location).to_track_quat('-Z','Y').to_euler()
    
def setup_day():
    w=bpy.data.worlds.new("day");sc.world=w;w.use_nodes=True;nt=w.node_tree;bg=nt.nodes["Background"]
    sk=nt.nodes.new("ShaderNodeTexSky");sk.sky_type='NISHITA';sk.sun_disc=False
    SUNDIR=Vector((0.55,-0.75,0.45)).normalized()   # towards the sun: front-right, ~27 deg up
    sk.sun_elevation=math.asin(SUNDIR.z);sk.sun_rotation=math.atan2(SUNDIR.x,SUNDIR.y)
    sk.air_density=1.0;sk.dust_density=1.5;sk.ozone_density=1.0;sk.altitude=50
    L(nt,sk.outputs[0],bg.inputs["Color"]);bg.inputs["Strength"].default_value=.22
    # light high cloud deck to soften (noise lerp to grey)
    sk.sun_disc=True;sk.sun_size=math.radians(.6);sk.sun_intensity=.4
    tc=nt.nodes.new("ShaderNodeTexCoord");sepz=N(nt,"ShaderNodeSeparateXYZ");L(nt,tc.outputs["Generated"],sepz.inputs[0])
    zc=math_(nt,'MAXIMUM',sepz.outputs["Z"],.02)
    px=math_(nt,'DIVIDE',sepz.outputs["X"],zc);py=math_(nt,'DIVIDE',sepz.outputs["Y"],zc)
    cv=N(nt,"ShaderNodeCombineXYZ");L(nt,px,cv.inputs[0]);L(nt,py,cv.inputs[1])
    nz=N(nt,"ShaderNodeTexNoise",Scale=.35,Detail=14.0,Roughness=.62,Distortion=.3);L(nt,cv.outputs[0],nz.inputs["Vector"])
    cm=N(nt,"ShaderNodeMapRange");cm.inputs[1].default_value=.5;cm.inputs[2].default_value=.72;L(nt,nz.outputs["Fac"],cm.inputs[0])
    hz=N(nt,"ShaderNodeMapRange");hz.inputs[1].default_value=.02;hz.inputs[2].default_value=.12;L(nt,sepz.outputs["Z"],hz.inputs[0])
    cf=math_(nt,'MULTIPLY',cm.outputs[0],hz.outputs[0])
    shade=N(nt,"ShaderNodeMapRange");shade.inputs[1].default_value=.55;shade.inputs[2].default_value=.85;shade.inputs[3].default_value=5.0;shade.inputs[4].default_value=2.6;L(nt,nz.outputs["Fac"],shade.inputs[0])
    ccol=N(nt,"ShaderNodeCombineColor");L(nt,shade.outputs[0],ccol.inputs[0]);L(nt,shade.outputs[0],ccol.inputs[1]);L(nt,math_(nt,'MULTIPLY',shade.outputs[0],1.04),ccol.inputs[2])
    cl=mixc(nt,math_(nt,'MULTIPLY',cf,.92),sk.outputs[0],ccol.outputs[0])
    lo=N(nt,"ShaderNodeMapRange");lo.inputs[1].default_value=-.01;lo.inputs[2].default_value=.15;lo.interpolation_type='SMOOTHSTEP';L(nt,sepz.outputs["Z"],lo.inputs[0])
    cl=mixc(nt,lo.outputs[0],(3.3,3.6,3.9,1),cl)
    L(nt,cl,bg.inputs["Color"])
    bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=4.0;sun.data.color=(1,.95,.87);sun.data.angle=math.radians(3)
    sun.rotation_euler=(-SUNDIR).to_track_quat('-Z','Y').to_euler()

if DAY: setup_day()
else: setup_night()
# ---------- RENDER ----------
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=SAMPLES;sc.cycles.use_denoising=True
sc.cycles.max_bounces=6;sc.cycles.volume_bounces=1;sc.cycles.volume_step_rate=4;sc.cycles.volume_max_steps=96
sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Punchy'
sc.view_settings.exposure=(0.0 if DAY else .6)
def cam(name,loc,target,lens):
    bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.name=name;c.data.lens=lens;c.data.clip_end=5000
    c.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler();return c
cams=[cam("Cam_Wide",(25,-125,9),(0,0,18),40),cam("Cam_Low",(-6,-36,4.5),(2,0,26),20),cam("Cam_Moon",(78,-70,34),(-4,10,9),30),cam("Cam_Gate",(6.5,-31,10),(2,-15,8.5),32)]
bpy.ops.wm.save_as_mainfile(filepath=OUT+"castle.blend")
only=ONLY
for c in cams:
    if only and c.name not in only: continue
    sc.camera=c;sc.render.filepath=OUT+f"{PFX}{c.name}.png";bpy.ops.render.render(write_still=True)
