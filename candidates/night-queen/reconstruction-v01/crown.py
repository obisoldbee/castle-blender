"""Separate candidate horned headdress. No exact archaeological back reconstruction claimed."""
import bpy, math
from mathutils import Vector

def rebuild_crown(stone):
    for o in list(bpy.data.objects):
        if o.name.startswith(('Continuous crown','Four pairs','Small crown top','R2 Crown')):
            bpy.data.objects.remove(o,do_unlink=True)
    made=[]
    def mesh(name,verts,faces):
        me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
        ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(stone)
        for f in me.polygons:f.use_smooth=True
        made.append(ob);return ob
    # Closed skull-following cap, intentionally behind all front horn tiers.
    N=64;M=20;vs=[];fs=[]
    for j in range(M+1):
        t=j/M; z=2.996+.242*t
        r=max(.018,(1-t**1.35)**.72)
        for i in range(N):
            a=2*math.pi*i/N
            vs.append((.150*r*math.cos(a),-.012+.145*r*math.sin(a),z))
    for j in range(M):
        for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
    fs.extend([tuple(range(N-1,-1,-1)),tuple(range(M*N,(M+1)*N))])
    mesh('R2 Crown continuous close cap',vs,fs)
    def bez(p,t):return p[0]*(1-t)**3+3*p[1]*t*(1-t)**2+3*p[2]*t*t*(1-t)+p[3]*t**3
    for level in range(4):
        width=[.177,.145,.113,.080][level]
        z=3.006+level*.056
        for sign in (-1,1):
            # Hook is broad at temporal root, flatter across brow, then turns upward at centre.
            points=[Vector((sign*width*.65,.055*(width/.177),z-.008)),Vector((sign*(width+.010),-.245,z-.008)),Vector((sign*.038,-.221,z-.020)),Vector((sign*.009,-.199,z+.068))]
            n=56;k=20;verts=[];faces=[]
            for i in range(n+1):
                t=i/n;c=bez(points,t)
                tangent=(bez(points,min(1,t+.001))-bez(points,max(0,t-.001))).normalized()
                depth=Vector((0,1,0));depth=(depth-tangent*depth.dot(tangent)).normalized();vertical=tangent.cross(depth).normalized()
                # Broad root and flattened horn blade, never equal-radius pipe.
                root=(1-t)**.65
                ry=.018*root+.002
                rz=.027*root+.002
                for h in range(k):
                    a=2*math.pi*h/k
                    verts.append(tuple(c+depth*(math.cos(a)*ry)+vertical*(math.sin(a)*rz)))
            for i in range(n):
                for h in range(k):faces.append((i*k+h,i*k+(h+1)%k,(i+1)*k+(h+1)%k,(i+1)*k+h))
            faces.extend([tuple(range(k-1,-1,-1)),tuple(range(n*k,(n+1)*k))])
            mesh('R2 Crown horn tier %d %s'%(level+1,'L' if sign<0 else 'R'),verts,faces)
    # Low-profile top disc is supported by the museum photograph description.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=16,location=(0,-.022,3.245))
    o=bpy.context.object;o.name='R2 Crown low top disc';o.scale=(.028,.027,.009);o.data.materials.append(stone)
    for f in o.data.polygons:f.use_smooth=True
    made.append(o)
    return made
