"""Rebuilt analytic carved head study, not a scan or archaeological reconstruction."""
import bpy, bmesh, math
from mathutils import Vector
from math import sin,cos,pi,exp,sqrt

def rebuild_face(stone):
    body=bpy.data.objects['GEO-body_female_realistic']
    # Remove previous modern head, retaining neck and all anatomy below cut.
    bm=bmesh.new();bm.from_mesh(body.data)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if (body.matrix_world@v.co).z>2.64],context='VERTS')
    bm.to_mesh(body.data);bm.free();body.data.update()
    for o in list(bpy.data.objects):
        if o.name.startswith(('Quiet carved eye','Rebuilt serene head','Upper eyelid','Lower eyelid','Fitted almond eye')):bpy.data.objects.remove(o,do_unlink=True)
    # z, halfwidth, depth radius, centre Y: rounded jaw, full cheek, smooth cranial cap.
    rows=[(2.595,.100,.100,-.010),(2.67,.090,.088,-.024),(2.70,.088,.082,-.035),
          (2.735,.119,.091,-.035),(2.78,.143,.105,-.020),(2.83,.157,.124,-.006),
          (2.88,.161,.138,.000),(2.93,.154,.145,.005),(2.98,.147,.145,.012),
          (3.025,.132,.129,.016),(3.065,.085,.087,.020),(3.085,.006,.007,.020)]
    def profile(z,k):
        for idx,(a,b) in enumerate(zip(rows,rows[1:])):
            if a[0]<=z<=b[0]:
                t=(z-a[0])/(b[0]-a[0]); span=b[0]-a[0]
                prev=rows[max(0,idx-1)]; nxt=rows[min(len(rows)-1,idx+2)]
                m0=(b[k]-prev[k])/(b[0]-prev[0]);m1=(nxt[k]-a[k])/(nxt[0]-a[0])
                return (2*t**3-3*t*t+1)*a[k]+(t**3-2*t*t+t)*span*m0+(-2*t**3+3*t*t)*b[k]+(t**3-t*t)*span*m1
        return rows[-1][k]
    def g(x,z,cx,cz,sx,sz):return exp(-((x-cx)/sx)**2-((z-cz)/sz)**2)
    vs=[];fs=[];N=160;K=192
    for i in range(N+1):
        z=rows[0][0]+(rows[-1][0]-rows[0][0])*i/N
        rx,ry,cy=[profile(z,k) for k in (1,2,3)]
        for j in range(K):
            a=2*pi*j/K;x=rx*sin(a);y=cy-ry*cos(a)
            if cos(a)>0:y=cy-ry*max(0,1-sin(a)**4)**.25
            front=max(0,cos(a))**5
            # Continuous orbital bowl and almond-shaped eyelid rim in same mesh.
            d=0.
            for s in (-1,1):
                u=(x-s*.067)/.043
                v=(z-(2.914+s*(x-s*.067)*.04))/.021
                # almond pointed corners rather than detached balls or empty circular holes
                e=(abs(u)**1.55+v*v)
                d+=.027*exp(-e*1.7)-.009*exp(-((sqrt(e)-1)/.18)**2)
                # soft brow arc, uninterrupted cheek pads
                browz=2.943+.009*(1-min(1,abs(u))**2)
                d-=.0055*exp(-((z-browz)/.010)**2-(u/1.25)**4)
                d-=.009*g(x,z,s*.083,2.864,.055,.035)
            # Distinct narrow bridge, softly rounded tip and alar volume.
            d-=.025*g(x,z,0,2.899,.022,.052)
            d-=.030*g(x,z,0,2.862,.027,.020)
            for s in (-1,1):
                d-=.013*g(x,z,s*.024,2.855,.012,.012)
                d+=.009*g(x,z,s*.018,2.850,.006,.0045)
            # Philtrum / mouth: gently lifted ends, formed lips not pasted curves.
            mouthz=2.802+.004*(min(1,abs(x)/.053)**1.7)
            envelope=exp(-(x/.055)**6)
            d-=envelope*(.011*exp(-((z-mouthz-.006)/.007)**2)+.012*exp(-((z-mouthz+.009)/.009)**2))
            d+=.009*envelope*exp(-((z-mouthz)/.0024)**2)
            d+=.003*g(x,z,0,2.825,.006,.015)
            d-=.008*g(x,z,0,2.754,.056,.025)
            y+=d*front
            vs.append((x,y,z))
    for i in range(N):
        for j in range(K):fs.append((i*K+j,i*K+(j+1)%K,(i+1)*K+(j+1)%K,(i+1)*K+j))
    fs.append(tuple(range(K-1,-1,-1)));fs.append(tuple(N*K+j for j in range(K)))
    mesh=bpy.data.meshes.new('Serene head continuous carved surface');mesh.from_pydata(vs,[],fs);mesh.update()
    ob=bpy.data.objects.new('Rebuilt serene head - continuous eyelid nose mouth',mesh);bpy.context.collection.objects.link(ob);mesh.materials.append(stone)
    for p in mesh.polygons:p.use_smooth=True
    from mathutils.kdtree import KDTree
    frontverts=[v for v in vs if v[1]<-.05]
    kd=KDTree(len(frontverts))
    for ix,v in enumerate(frontverts):kd.insert((v[0],v[2],0),ix)
    kd.balance()
    def skin_y(x,z):
        co,ix,dist=kd.find((x,z,0));return frontverts[ix][1]
    # Fitted almond eye surfaces and tapering lids; no free-floating spherical eyes.
    for side in (-1,1):
        cx=side*.067;cz=2.914;w=.041
        for upper in (True,False):
            cu=bpy.data.curves.new('Sculpted upper lid' if upper else 'Sculpted lower lid','CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=.006 if upper else .004;cu.bevel_resolution=3
            sp=cu.splines.new('POLY');sp.points.add(32)
            for i,p in enumerate(sp.points):
                u=-1+2*i/32;arc=max(0,1-u*u)**.8
                zz=cz+(.018 if upper else -.012)*arc
                p.co=(cx+w*u,skin_y(cx+w*u,zz)-.0015,zz,1);p.radius=.18+.82*arc
            lid=bpy.data.objects.new(('Upper eyelid' if upper else 'Lower eyelid')+str(side),cu);bpy.context.collection.objects.link(lid);cu.materials.append(stone)
        ev=[];ef=[]
        for i in range(33):
            u=-1+2*i/32;arc=max(0,1-u*u)**.8
            for j in range(13):
                v=j/12
                zz=cz+arc*(-.012+.030*v)
                ev.append((cx+w*u,skin_y(cx+w*u,zz)-.001,zz))
        for i in range(32):
            for j in range(12):ef.append((i*13+j,(i+1)*13+j,(i+1)*13+j+1,i*13+j+1))
        em=bpy.data.meshes.new('Almond carved eye surface');em.from_pydata(ev,[],ef);em.materials.append(stone);eo=bpy.data.objects.new('Fitted almond eye '+str(side),em);bpy.context.collection.objects.link(eo)
        for p in em.polygons:p.use_smooth=True
    ob['interpretation']='Modern sculptural reconstruction from front photo; not a scan. Head/neck joint needs final topology integration.'
    return ob
