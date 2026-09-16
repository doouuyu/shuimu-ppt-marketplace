import copy
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/editable-ppt/scripts/validate_deck.py'


def minimal_plan():
    return {
        'workflow': 'editable-ppt', 'canvas': {'width': 1280, 'height': 720, 'unit': 'px'},
        'assets': [], 'slides': [{'id': 'P01', 'role': 'content', 'elements': [{
            'id': 'P01-title', 'type': 'text', 'box': [48, 32, 1150, 72], 'z': 2,
            'text': '可编辑标题', 'font_family': 'Arial', 'font_size_pt': 32,
            'bold': True, 'color': '#10367D', 'align': 'left', 'valign': 'middle',
            'margin_px': [0, 0, 0, 0], 'line_spacing': 1.15, 'paragraph_after_pt': 0,
        }]}],
    }


class EditableWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('editable_check', SCRIPT)
        cls.check = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.check)

    def test_accepts_explicit_native_text_plan(self):
        self.assertEqual([], self.check.validate_plan(minimal_plan(), Path('.')))

    def test_rejects_out_of_bounds(self):
        plan = minimal_plan()
        plan['slides'][0]['elements'][0]['box'] = [1200, 0, 200, 70]
        self.assertTrue(self.check.validate_plan(plan, Path('.')))

    def test_rejects_duplicate_ids(self):
        plan = minimal_plan()
        plan['slides'][0]['elements'].append(copy.deepcopy(plan['slides'][0]['elements'][0]))
        self.assertTrue(self.check.validate_plan(plan, Path('.')))

    def test_rejects_missing_font_and_alignment(self):
        plan = minimal_plan()
        del plan['slides'][0]['elements'][0]['font_size_pt']
        del plan['slides'][0]['elements'][0]['align']
        self.assertTrue(self.check.validate_plan(plan, Path('.')))

    def test_rejects_missing_asset_file(self):
        plan = minimal_plan()
        plan['assets'] = [{'id': 'A01', 'path': 'never-exists.png', 'kind': 'illustration',
                           'source': 'generated', 'text_free': True}]
        plan['slides'][0]['elements'].append({'id': 'P01-img', 'type': 'image', 'box': [50, 150, 400, 300],
                                              'z': 1, 'asset_id': 'A01', 'fit': 'contain'})
        self.assertTrue(self.check.validate_plan(plan, Path('.'), require_assets=True))
        self.assertEqual([], self.check.validate_plan(plan, Path('.')))

    def test_rejects_generated_asset_with_baked_text(self):
        plan = minimal_plan()
        plan['assets'] = [{'id': 'A01', 'path': 'a.png', 'kind': 'illustration',
                           'source': 'generated', 'text_free': False}]
        self.assertTrue(self.check.validate_plan(plan, Path('.')))

    def test_bundled_example_is_a_valid_detailed_plan(self):
        import json
        path = ROOT / 'skills/editable-ppt/references/layout-example.json'
        plan = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual([], self.check.validate_plan(plan, path.parent))

    def test_rejects_table_dimensions_that_exceed_frame(self):
        plan = minimal_plan()
        plan['slides'][0]['elements'].append({
            'id': 'P01-table', 'type': 'table', 'box': [48, 160, 600, 200], 'z': 2,
            'font_family': 'Arial', 'font_size_pt': 18, 'rows': [['A', 'B'], ['1', '2']],
            'column_widths': [400, 400], 'row_heights': [100, 100],
        })
        self.assertTrue(self.check.validate_plan(plan, Path('.')))

    def test_rejects_chart_series_with_wrong_category_count(self):
        plan = minimal_plan()
        plan['slides'][0]['elements'].append({
            'id': 'P01-chart', 'type': 'chart', 'box': [48, 160, 600, 200], 'z': 2,
            'font_family': 'Arial', 'font_size_pt': 18, 'chart_type': 'bar',
            'categories': ['A', 'B'], 'series': [{'name': '示例', 'values': [1]}],
        })
        self.assertTrue(self.check.validate_plan(plan, Path('.')))

    def make_package(self, path, slide_body):
        with zipfile.ZipFile(path, 'w') as deck:
            deck.writestr('ppt/presentation.xml', '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>')
            deck.writestr('ppt/_rels/presentation.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="slides/slide1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"/></Relationships>')
            deck.writestr('ppt/slides/slide1.xml', '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree>' + slide_body + '</p:spTree></p:cSld></p:sld>')

    def test_pptx_requires_named_native_text_not_picture(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.pptx'
            self.make_package(path, '<p:pic><p:nvPicPr><p:cNvPr id="2" name="P01-title"/></p:nvPicPr></p:pic>')
            self.assertTrue(self.check.audit_pptx(minimal_plan(), path))

    def test_pptx_text_matches_and_is_not_hidden(self):
        body = '<p:sp><p:nvSpPr><p:cNvPr id="2" name="P01-title"/></p:nvSpPr><p:txBody><a:p><a:r><a:t>可编辑标题</a:t></a:r></a:p></p:txBody></p:sp>'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.pptx'
            self.make_package(path, body)
            self.assertEqual([], self.check.audit_pptx(minimal_plan(), path))
            self.make_package(path, body.replace('name="P01-title"', 'name="P01-title" hidden="1"'))
            self.assertTrue(self.check.audit_pptx(minimal_plan(), path))
            self.make_package(path, body.replace('可编辑标题', '另一份标题'))
            self.assertTrue(self.check.audit_pptx(minimal_plan(), path))


if __name__ == '__main__':
    unittest.main()
