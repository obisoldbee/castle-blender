"""Parser-only regression: no Blender scene mutation or files are needed."""
import ast,argparse,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SourcePreflight(unittest.TestCase):
 def parser(self,name):
  tree=ast.parse((ROOT/name).read_text())
  node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse_options')
  ns={'argparse':argparse,'Path':Path}
  exec(compile(ast.Module(body=[node],type_ignores=[]),name,'exec'),ns)
  return ns['parse_options']
 def test_invalid_samples(self):
  for f in ('castle/castle.py','castle/gargoyle_closeups/shots.py'):
   with self.subTest(f=f),self.assertRaises(SystemExit):
    self.parser(f)(['0','--output-dir','unused'])
 def test_invalid_camera(self):
  with self.assertRaises(SystemExit): self.parser('castle/castle.py')(['64','BAD','--output-dir','unused'])
 def test_build_only(self):
  self.assertEqual(self.parser('castle/castle.py')(['--output-dir','unused']).mode,'build')
  self.assertEqual(self.parser('castle/gargoyle_closeups/shots.py')(['--output-dir','unused']).mode,'prepare')
if __name__=='__main__': unittest.main()
