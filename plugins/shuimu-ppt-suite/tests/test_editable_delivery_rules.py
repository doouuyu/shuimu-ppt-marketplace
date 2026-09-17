import copy
import tempfile
import unittest
from pathlib import Path

import test_editable_workflow as existing
from test_editable_workflow import minimal_plan, ROOT


def delivery_plan():
    plan = minimal_plan()
    plan['style'] = {'id': 'neutral', 'reference_kind': 'none', 'explicitly_requested': False}
    plan['assets'] = [{'id': 'A01', 'path': 'a.png', 'kind': 'decoration',
                       'purpose': 'decorative', 'source': 'generated', 'text_free': True,
                       'prompt': '无文字柔和蓝色波纹装饰', 'status': 'planned'}]
    plan['slides'][0]['elements'] = [plan['slides'][0]['elements'][0], {
        'id': 'P01-art', 'type': 'image', 'asset_id': 'A01', 'fit': 'contain',
        'box': [880, 300, 300, 250], 'z': 1}]
    return plan


class EditableDeliveryRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        existing.EditableWorkflowTest.setUpClass()
        cls.check = existing.EditableWorkflowTest.check

    def errors(self, plan, require_assets=False):
        return self.check.validate_plan(plan, Path('.'), require_assets)

    def native_plan(self, profile='aihia'):
        plan = delivery_plan()
        folder = 'aihia' if profile == 'aihia' else 'artifact-template-shuimu-qinglv-ppt'
        plan['style'] = {'id': profile, 'reference_kind': 'native-template',
                         'reference_path': str(ROOT / 'skills' / folder / 'assets/reference.pptx'),
                         'explicitly_requested': True}
        plan['slides'][0]['role'] = 'cover'
        plan['slides'][0]['template_source'] = {
            'slide': 1, 'mode': 'duplicate-slide',
            'preserve': ['theme', 'layout', 'background', 'logo', 'title-style']}
        return plan

    def test_valid_designed_decoration_passes_preflight(self):
        self.assertEqual([], self.errors(delivery_plan()))

    def test_empty_assets_cannot_skip_generation(self):
        plan = delivery_plan()
        plan['assets'] = []
        plan['slides'][0]['elements'] = plan['slides'][0]['elements'][:1]
        self.assertTrue(self.errors(plan))

    def test_existing_photo_does_not_replace_generation_stage(self):
        plan = delivery_plan()
        plan['assets'][0]['source'] = 'user'
        self.assertTrue(self.errors(plan))

    def test_generated_but_unused_decoration_is_rejected(self):
        plan = delivery_plan()
        plan['slides'][0]['elements'] = plan['slides'][0]['elements'][:1]
        self.assertTrue(self.errors(plan))

    def test_each_content_page_has_visual_asset(self):
        plan = delivery_plan()
        slide = copy.deepcopy(plan['slides'][0])
        slide.update(id='P02', elements=[dict(slide['elements'][0], id='P02-title')])
        plan['slides'].append(slide)
        self.assertTrue(self.errors(plan))

    def test_pixel_style_requires_explicit_selection(self):
        plan = delivery_plan()
        plan['style']['id'] = 'pixel-defense-academic-ppt'
        self.assertTrue(self.errors(plan))

    def test_native_templates_require_reference_and_inheritance(self):
        for profile in ('aihia', 'shuimu-qinglv'):
            with self.subTest(profile=profile):
                plan = self.native_plan(profile)
                self.assertEqual([], self.errors(plan))
                del plan['slides'][0]['template_source']
                self.assertTrue(self.errors(plan))

    def test_native_cover_cannot_be_redrawn(self):
        plan = self.native_plan()
        plan['slides'][0]['template_source']['mode'] = 'reconstruct-editable'
        self.assertTrue(self.errors(plan))

    def test_aihia_section_uses_actual_section_slide(self):
        plan = self.native_plan()
        plan['slides'][0]['role'] = 'section'
        self.assertTrue(self.errors(plan))
        plan['slides'][0]['template_source']['slide'] = 4
        self.assertEqual([], self.errors(plan))

    def test_aihia_cannot_silently_use_qinglv_template(self):
        plan = self.native_plan('shuimu-qinglv')
        plan['style']['id'] = 'aihia'
        self.assertTrue(self.errors(plan))

    def test_declared_native_reference_cannot_be_missing(self):
        plan = self.native_plan()
        plan['style']['reference_path'] = 'missing-template.pptx'
        self.assertTrue(self.errors(plan))

    def test_placeholders_are_rejected_in_final_copy(self):
        for text in ('数据待补充', '示意数据：86%', '演示数据：100例', '请输入标题', 'TBD', 'XXX医院'):
            with self.subTest(text=text):
                plan = delivery_plan()
                plan['slides'][0]['elements'][0]['text'] = text
                self.assertTrue(self.errors(plan))

    def test_real_qualifiers_and_external_review_gaps_are_allowed(self):
        plan = delivery_plan()
        plan['slides'][0]['elements'][0]['text'] = '建设目标与预测范围'
        plan['review_gaps'] = [{'page': 'P01', 'missing': '待补充病例数', 'action': 'omitted'}]
        self.assertEqual([], self.errors(plan))

    def test_hard_corner_content_panels_rejected_by_default(self):
        plan = delivery_plan()
        plan['slides'][0]['elements'].append({
            'id': 'P01-box', 'type': 'shape', 'geometry': 'rect', 'purpose': 'content-panel',
            'box': [50, 150, 300, 300], 'z': 0})
        self.assertTrue(self.errors(plan))

    def test_reused_template_header_may_keep_square_corners(self):
        plan = self.native_plan()
        plan['slides'][0]['elements'].append({
            'id': 'P01-header', 'type': 'shape', 'geometry': 'rect', 'purpose': 'template',
            'box': [0, 0, 1280, 80], 'z': 0})
        self.assertEqual([], self.errors(plan))

    def test_real_image_file_not_just_existing_filename_required(self):
        plan = delivery_plan()
        plan['assets'][0].update(status='accepted', width_px=10, height_px=10)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'a.png'
            path.write_text('not an image')
            self.assertTrue(self.check.validate_plan(plan, Path(tmp), True))

    def test_accepted_real_image_can_enter_assembly(self):
        plan = delivery_plan()
        path = ROOT / 'skills/pixel-defense-academic-ppt/assets/calibrated-content-example.png'
        plan['assets'][0].update(path=str(path), status='accepted', width_px=1672, height_px=941)
        self.assertEqual([], self.errors(plan, require_assets=True))

    def test_existing_image_without_acceptance_cannot_enter_assembly(self):
        plan = delivery_plan()
        path = ROOT / 'skills/pixel-defense-academic-ppt/assets/calibrated-content-example.png'
        plan['assets'][0].update(path=str(path), width_px=1672, height_px=941)
        self.assertTrue(self.errors(plan, require_assets=True))

    def test_template_bleed_is_preserved_only_with_source_mapping(self):
        plan = self.native_plan()
        art = plan['slides'][0]['elements'][1]
        art.update(box=[0, -8, 1280, 736], template_bleed=True, source_object='Original background')
        self.assertEqual([], self.errors(plan))
        del art['source_object']
        self.assertTrue(self.errors(plan))

    def test_temporary_numbers_cannot_be_hidden_by_removing_placeholder_label(self):
        plan = delivery_plan()
        plan['slides'][0]['elements'][0].update(text='病例数 1000', data_status='temporary')
        self.assertTrue(self.errors(plan))

    def test_explicit_image_reference_style_can_use_square_panels(self):
        plan = delivery_plan()
        plan['style'] = {
            'id': 'pixel-defense-academic-ppt', 'explicitly_requested': True,
            'reference_kind': 'image-reference',
            'reference_path': str(ROOT / 'skills/pixel-defense-academic-ppt/assets/content-layout-reference.png')}
        plan['slides'][0]['reference_anchor'] = '内容页图版左上样本'
        plan['slides'][0]['elements'].append({
            'id': 'P01-box', 'type': 'shape', 'geometry': 'rect', 'purpose': 'content-panel',
            'box': [50, 150, 300, 300], 'z': 0})
        self.assertEqual([], self.errors(plan))

    def test_unplanned_template_placeholder_in_pptx_is_rejected(self):
        plan = delivery_plan()
        plan['slides'][0]['elements'] = plan['slides'][0]['elements'][:1]
        body = '<p:sp><p:nvSpPr><p:cNvPr id="2" name="P01-title"/></p:nvSpPr><p:txBody><a:p><a:r><a:t>可编辑标题</a:t></a:r></a:p></p:txBody></p:sp>'
        body += '<p:sp><p:txBody><a:p><a:r><a:t>请输入标题</a:t></a:r></a:p></p:txBody></p:sp>'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.pptx'
            existing.EditableWorkflowTest().make_package(path, body)
            self.assertTrue(self.check.audit_pptx(plan, path))
