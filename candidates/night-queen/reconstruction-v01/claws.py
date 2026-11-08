"""Candidate claw rebuilding: source-informed three visible front toes, not a scan.
Run rebuild_claws(stone) after loading candidate. World units metres.
Foot roots at ±0.14; body's shins must be moved correspondingly by caller.
"""
import bpy, math
from mathutils import Vector
from math import sin,cos,pi,exp

def mesh_obj(name,verts,faces,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    return ob

def lerp_stations(st,t):
    q=t*(len(st)-1);i=min(int(q),len(st)-2);a=q-i
    return st[i].lerp(st[i+1],a)

def tube(name,pts,radius,mat,n=90,k=32,grooves=()):
    st=[Vector(p) for p in pts];vs=[];fs=[]
    for i in range(n+1):
        t=i/n;c=lerp_stations(st,t)
        tangent=(lerp_stations(st,min(1,t+.001))-lerp_stations(st,max(0,t-.001))).normalized()
        u=Vector((1,0,0));u=(u-u.dot(tangent)*tangent).normalized();v=u.cross(tangent).normalized()
        if v.z<0:v=-v
        r=radius(t)
        for j in range(k):
            a=2*pi*j/k;upper=max(0,sin(a))**1.7
            incision=sum(.0030*exp(-((t-g-.007*cos(a*2))/.009)**2) for g in grooves)*upper
            p=c+u*cos(a)*(r-incision)+v*sin(a)*(r-incision)*.83
            # Broad plantar plane makes contact explicit, not floating claw tips.
            p.z=max(.3102,p.z)
            vs.append(tuple(p))
    for i in range(n):
        for j in range(k):fs.append((i*k+j,i*k+(j+1)%k,(i+1)*k+(j+1)%k,(i+1)*k+j))
    fs.extend([tuple(range(k-1,-1,-1)),tuple(range(n*k,(n+1)*k))])
    return mesh_obj(name,vs,fs,mat)

def root(cx,mat):
    # Elliptical loft: rounded heel, broad dorsal foot, continuous taper to shin.
    levels=[(.347,-.025,.044,.055),(.377,-.021,.069,.071),(.412,-.005,.072,.075),(.445,.007,.064,.068),(.478,.016,.052,.058),(.513,.020,.046,.052),(.548,.022,.044,.051)]
    vs=[];fs=[];k=48
    for z,y,rx,ry in levels:
        for j in range(k):
            a=2*pi*j/k;vs.append((cx+rx*cos(a),y+ry*sin(a),z))
    for i in range(len(levels)-1):
        for j in range(k):fs.append((i*k+j,i*k+(j+1)%k,(i+1)*k+(j+1)%k,(i+1)*k+j))
    fs.extend([tuple(range(k-1,-1,-1)),tuple(range((len(levels)-1)*k,len(levels)*k))])
    return mesh_obj('Rebuilt broad tarsus',vs,fs,mat)

def rebuild_claws(stone):
    prefixes=('Bird ankle transition','Ankle carved ring','Tapered avian talon','Thick articulated toe','Rebuilt claw','Rebuilt broad','Rebuilt bird foot')
    for o in list(bpy.data.objects):
        if o.name.startswith(prefixes):bpy.data.objects.remove(o,do_unlink=True)
    result=[]
    for s in (-1,1):
        cx=s*.14;parts=[root(cx,stone)]
        for j in (-1,0,1):
            length=.265 if j==0 else (.235 if j==s else .245)
            ex=cx+j*.080
            pts=[(cx+j*.037,-.025,.421),(cx+j*.052,-.090,.404),(ex,-.155,.371),(ex+j*.006,-length+.030,.347),(ex+j*.007,-length,.343)]
            def rad(t):
                return .032*(1-.24*t)+.007*exp(-((t-.24)/.125)**2)+.009*exp(-((t-.57)/.115)**2)+.006*exp(-((t-.84)/.100)**2)
            parts.append(tube('Rebuilt claw toe',pts,rad,stone,grooves=(.16,.205,.29,.47,.515,.62,.77,.81,.9)))
            parts.append(tube('Rebuilt claw nail',[(ex+j*.007,-length+.009,.348),(ex+j*.008,-length-.017,.345),(ex+j*.009,-length-.038,.327),(ex+j*.009,-length-.047,.311)],lambda t:.017*(1-t)**.75+.0008,stone,n=28,k=20))
        bpy.ops.object.select_all(action='DESELECT')
        for ob in parts:ob.select_set(True)
        bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();foot=parts[0];foot.name='Rebuilt bird foot.'+('L' if s<0 else 'R')
        rem=foot.modifiers.new('Continuous foot union','REMESH');rem.mode='VOXEL';rem.voxel_size=.0016;rem.use_smooth_shade=True
        bpy.ops.object.modifier_apply(modifier=rem.name)
        smooth=foot.modifiers.new('Soften union transitions','SMOOTH');smooth.factor=.55;smooth.iterations=3;bpy.ops.object.modifier_apply(modifier=smooth.name)
        # Shallow transverse ankle creases carved into the connected skin, not rings.
        for vert in foot.data.vertices:
            x,y,z=vert.co
            if z>.442 and y<.022:
                front=max(0,min(1,(.022-y)/.045))
                dz=sum(.0018*exp(-((z-g-.0015*cos((x-cx)*55))/.0020)**2) for g in (.449,.460,.473,.484,.500))
                vert.co.y+=front*dz
            vert.co.z=max(.3102,vert.co.z)
        for poly in foot.data.polygons:poly.use_smooth=True
        foot['reference']='Burney Relief lions photo by Fæ, CC BY-SA 3.0; modern 3D interpretation'
        foot['contact_plane_z']=.3102;result.append(foot)
    return result
