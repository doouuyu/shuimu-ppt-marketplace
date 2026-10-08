import hashlib
import importlib.util
import json
import unittest
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SID = 'pixel-defense-academic-ppt'
EXPECTED_HASH = None

class ReusableStyleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('selection_'+SID, ROOT/'shared/resolve_selection.py')
        cls.resolver=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.resolver)
        cls.style=next(s for s in json.loads((ROOT/'styles/catalog.json').read_text())['styles'] if s['id']==SID)

    def test_every_production_mode_can_select_this_style(self):
        for mode in ('editable-ppt','ppt-image-deck','native-template-ppt'):
            choice=self.resolver.resolve(mode, self.style['name'])
            self.assertEqual(mode,choice['workflow'])
            self.assertEqual(SID,choice['style']['id'])

    def test_alias_selects_resource_without_changing_mode(self):
        for alias in self.style.get('aliases',[]):
            choice=self.resolver.resolve(style=alias)
            self.assertEqual('editable-ppt',choice['workflow'])
            self.assertEqual(SID,choice['style']['id'])

    def test_retained_reference_and_guide_are_real(self):
        self.assertTrue((ROOT/'styles'/self.style['guide']).is_file())
        if 'reference' in self.style:
            ref=ROOT/'styles'/self.style['reference']
            self.assertTrue(ref.is_file())
            if ref.suffix=='.pptx':
                with zipfile.ZipFile(ref) as archive:self.assertIn('ppt/presentation.xml',archive.namelist())
        if EXPECTED_HASH:
            filename='visual_reference' if SID=='qinghua-changgung-blue' else 'reference'
            ref=ROOT/'styles'/self.style[filename]
            self.assertEqual(EXPECTED_HASH,hashlib.sha256(ref.read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()
