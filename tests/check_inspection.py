"""Fail fast on published-scene acceptance invariants from inspect_scene.py."""
import json,sys,math
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
assert r['active_camera'], 'missing active camera'
assert r['samples']>=16, 'preview samples saved in release scene'
assert r['output'].startswith('//'), 'saved output must be Blender-relative'
assert not r['texts'] and not r['drivers'] and not r['external_libraries'], 'unexpected executable/external dependency'
assert len(r['finials'])==24, f"expected 24 finial contacts, got {len(r['finials'])}"
assert max(p['gap'] for p in r['finials'])<=.001, 'floating finial'
if 'frames' in r:
 a,b=r['frames']['1'],r['frames']['721']
 for key in ('camera','moon'):
  assert math.dist(a[key],b[key])<1e-4,(key,a[key],b[key])
 assert abs(a['lens']-b['lens'])<1e-5
 assert abs(a['exposure']-b['exposure'])<1e-5
 # q and -q describe same rotation.
 assert abs(abs(sum(x*y for x,y in zip(a['camera_rotation'],b['camera_rotation'])))-1)<1e-5
 assert math.dist(r['frames']['719']['camera'],r['frames']['720']['camera'])>.001,'frozen tail'
print('PASS',sys.argv[1])
