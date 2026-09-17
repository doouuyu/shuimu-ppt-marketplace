import unittest
from pathlib import Path

import test_editable_workflow as existing


class ProjectionReadabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        existing.EditableWorkflowTest.setUpClass()
        cls.check = existing.EditableWorkflowTest.check

    def plan(self, **changes):
        plan = existing.minimal_plan()
        plan['readability_profile'] = 'projection'
        plan['slides'][0]['elements'][0].update(
            text_role='body', font_size_pt=22, bold=True, color='#111111')
        plan['slides'][0]['elements'][0].update(changes)
        return plan

    def errors(self, plan):
        return self.check.validate_plan(plan, Path('.'))

    def test_large_bold_dark_body_passes(self):
        self.assertEqual([], self.errors(self.plan()))

    def test_small_body_rejected(self):
        self.assertTrue(self.errors(self.plan(font_size_pt=20)))

    def test_small_title_rejected(self):
        self.assertTrue(self.errors(self.plan(text_role='title', font_size_pt=32)))

    def test_gray_and_gray_blue_text_rejected(self):
        for color in ('#777777', '#5A6878', '#20262E', '#CCCCCC'):
            with self.subTest(color=color):
                self.assertTrue(self.errors(self.plan(color=color)))

    def test_regular_weight_rejected(self):
        self.assertTrue(self.errors(self.plan(bold=False)))

    def test_white_on_brand_purple_passes(self):
        self.assertEqual([], self.errors(self.plan(color='#FFFFFF', background_color='#694CD5')))

    def test_low_contrast_color_rejected(self):
        self.assertTrue(self.errors(self.plan(color='#FFCC00')))

    def test_translucent_text_rejected(self):
        self.assertTrue(self.errors(self.plan(opacity=0.5)))

    def test_small_gray_run_cannot_bypass_parent_style(self):
        self.assertTrue(self.errors(self.plan(runs=[{'text': '可编辑标题', 'font_size_pt': 16, 'color': '#888888'}])))

    def test_table_styles_are_checked(self):
        plan = self.plan()
        plan['slides'][0]['elements'].append({
            'id': 'P01-table', 'type': 'table', 'box': [40, 160, 600, 200], 'z': 1,
            'font_family': 'Arial', 'font_size_pt': 22, 'bold': True,
            'rows': [['对象', '用途'], ['标题', '说明']], 'column_widths': [300, 300],
            'row_heights': [100, 100], 'header_fill': '#10367D', 'header_color': '#FFFFFF',
            'body_fill': '#FFFFFF', 'body_color': '#111111', 'alternate_fill': '#EAF2FA'})
        self.assertEqual([], self.errors(plan))
        plan['slides'][0]['elements'][-1]['text_styles'] = [{'text_role': 'label', 'font_size_pt': 24}]
        self.assertEqual([], self.errors(plan))
        plan['slides'][0]['elements'][-1]['body_color'] = '#888888'
        self.assertTrue(self.errors(plan))

    def test_chart_label_override_checked(self):
        plan = self.plan()
        plan['slides'][0]['elements'].append({
            'id': 'P01-chart', 'type': 'chart', 'box': [40, 160, 600, 300], 'z': 1,
            'font_family': 'Arial', 'font_size_pt': 22, 'bold': True, 'color': '#111111',
            'chart_type': 'bar', 'categories': ['A'], 'series': [{'name': '样本', 'values': [1]}],
            'source_ref': 'test fixture', 'text_styles': [{'role': 'label', 'font_size_pt': 12}]})
        self.assertTrue(self.errors(plan))

    def test_larger_canvas_does_not_shrink_relative_type(self):
        plan = self.plan()
        plan['canvas'].update(width=2560, height=1440)
        self.assertTrue(self.errors(plan))

    def test_footnote_has_explicit_floor(self):
        self.assertEqual([], self.errors(self.plan(text_role='footnote', font_size_pt=18)))
        self.assertTrue(self.errors(self.plan(text_role='footnote', font_size_pt=16)))


class ScreenReadabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        existing.EditableWorkflowTest.setUpClass()
        cls.check = existing.EditableWorkflowTest.check

    plan = ProjectionReadabilityTest.plan
    errors = ProjectionReadabilityTest.errors

    def test_screen_is_default_and_allows_regular_dark_gray(self):
        plan = self.plan(font_size_pt=20, bold=False, color='#4B5565')
        plan.pop('readability_profile')
        self.assertEqual([], self.errors(plan))

    def test_screen_title_and_table_sizes_are_not_projection_sizes(self):
        plan = self.plan(text_role='title', font_size_pt=30, bold=True, color='#172033')
        plan['readability_profile'] = 'screen'
        self.assertEqual([], self.errors(plan))
        plan['slides'][0]['elements'][0].update(text_role='label', font_size_pt=18, bold=False)
        self.assertEqual([], self.errors(plan))

    def test_screen_still_rejects_unreadable_text(self):
        plan = self.plan(font_size_pt=16, bold=False, color='#4B5565')
        plan['readability_profile'] = 'screen'
        self.assertTrue(self.errors(plan))

    def test_projection_is_opt_in(self):
        self.assertTrue(self.errors(self.plan(font_size_pt=20, bold=False, color='#4B5565')))

    def test_unknown_profile_is_rejected(self):
        plan = self.plan()
        plan['readability_profile'] = 'other'
        self.assertTrue(self.errors(plan))
