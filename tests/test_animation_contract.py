"""Pure-Python checks of the preflight and continuous authored trajectory.

AST extraction deliberately excludes all Blender imports and execution.
"""
import argparse
import ast
import math
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'castle' / 'anim.py'
TREE = ast.parse(SOURCE.read_text())
NAMES = {'F0','F1','FEND','TODK','CP'}
FUNCTIONS = {'positive_int','parse_options','phase','ocean_state','tod','moon_elevation','lerp','ease','camstate'}
parts=[]
for node in TREE.body:
    if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS:
        parts.append(node)
    if isinstance(node,ast.Assign):
        names={n.id for t in node.targets for n in ast.walk(t) if isinstance(n,ast.Name)}
        if names and names <= NAMES:
            parts.append(node)
scope=dict(argparse=argparse,math=math,re=re,Path=Path,__file__=str(SOURCE))
exec(compile(ast.Module(body=parts,type_ignores=[]),str(SOURCE),'exec'),scope)

class Contract(unittest.TestCase):
    def test_default_build_never_renders(self):
        opt=scope['parse_options']([])
        self.assertEqual(opt.mode,'build');self.assertFalse(opt.render)
    def test_invalid_params(self):
        for args in [['bogus'],['--samples','0'],['--start','721'],['--start','5','--end','2'],['--keys','../../bad:2'],['--build-id','../bad'],['build','--render']]:
            with self.assertRaises(SystemExit): scope['parse_options'](args)
    def test_closed_endpoints(self):
        self.assertAlmostEqual(scope['tod'](721)-scope['tod'](1),24)
        self.assertAlmostEqual(scope['moon_elevation'](721),scope['moon_elevation'](1))
        self.assertEqual(scope['camstate'](721),scope['camstate'](1))
        for offset in (0,.5): self.assertEqual(scope['ocean_state'](721,offset),scope['ocean_state'](1,offset))
    def test_ocean_weights(self):
        for f in range(1,722):
            _,a=scope['ocean_state'](f,0);_,b=scope['ocean_state'](f,.5)
            self.assertAlmostEqual(a+b,1)
        for offset,reset in [(0,721),(.5,361)]:
            self.assertAlmostEqual(scope['ocean_state'](reset,offset)[1],0)
    def test_no_static_tail(self):
        # Orbit angle still advances regardless of the radius easing.
        self.assertNotEqual(scope['phase'](719),scope['phase'](720))
        self.assertNotEqual(scope['ocean_state'](719),scope['ocean_state'](720))
    def test_preflight_before_blender_import(self):
        source=SOURCE.read_text()
        self.assertLess(source.index('OPTIONS = parse_options'),source.index('import bpy'))
        self.assertIn('exist_ok=False',source)
        self.assertIn("sc.render.use_placeholder=False",source)
        self.assertIn("sc.get(\"castle_animation_version\")",source)

if __name__=='__main__': unittest.main()
