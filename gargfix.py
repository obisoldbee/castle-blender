# In-memory fix for anim/castle_24h.blend (not saved): mirrors castle.py v17 gargoyle fix.
import bpy,bmesh,math
from mathutils import Vector,Matrix
OFF=Vector((1,0,3.6))
def mounts():
    M=[]
    for a in (-math.pi/2-.55,-math.pi/2+.55):
        M.append(dict(kind='tower',c=Vector((3,4,0))+OFF,a=a,r=2.6,z=27+3.6,s=1.9))
    for s_ in (1,-1):
        for yy in (-1,2,5):
            M.append(dict(kind='pier',base=Vector((s_*13.8,yy,15.8))+OFF,a=0 if s_>0 else math.pi,s=1.15))
    for m in M:
        if m['kind']=='tower':
            ca,sa=math.cos(m['a']),math.sin(m['a'])
            m['old']=m['c']+Vector((ca*m['r']*1.12,sa*m['r']*1.12,0));m['old'].z=m['z']
            m['base']=m['c']+Vector((ca*m['r'],sa*m['r'],0));m['base'].z=m['z']
        else: m['old']=m['base']
    return M
def bbox(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
    return (lo+hi)/2,hi-lo
def parts(m):
    out=[]
    for o in bpy.data.objects:
        if o.type!='MESH' or not o.data.materials or o.data.materials[0] is None or o.data.materials[0].name!='stone': continue
        if not o.name.split('.')[0] in ('Cone','Sphere','wing','Cylinder'): continue
        c,d=bbox(o)
        if max(d)<1.7*m['s'] and (c-m['old']).length<1.35*m['s']: out.append(o)
    return out
def corbel(m):
    s,a=m['s'],m['a'];ca,sa=math.cos(a),math.sin(a);b=m['base']
    loc=b+Vector((ca*.1*s,sa*.1*s,-.12*s))
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=(0,0,a));o=bpy.context.object
    o.scale=(.95*s/2,.38*s/2,.32*s/2);o.data.materials.append(bpy.data.materials['dstone']);o.name='garg_corbel'
    return o
def apply():
    for m in mounts():
        ps=parts(m);sh=m['base']-m['old']
        for o in ps: o.matrix_world=Matrix.Translation(sh)@o.matrix_world
        corbel(m);print('GARGFIX',m['kind'],round(m['a'],2),len(ps),'parts moved',tuple(round(v,2) for v in sh))
if __name__=="__main__": apply()
