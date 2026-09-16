import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'skills/pixel-defense-academic-ppt/scripts/check_prompts.py'


class PromptPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('pixel_check', PATH)
        cls.check = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.check)

    def document(self, theme='blue'):
        prefix = self.check.style_prefix(theme)
        return '\n'.join(f'''## P{i:02d}｜研究背景
```text
{prefix}
页面角色：content
页面家族：背景/差距页
标题系统：全宽顶部标题条
密度级别：密
版式：顶栏占高9%，下方结论，两列证据，右图占主体55%。
证据图版：用户提供的入组表与流程对照，禁止补造数据。
顶部结论句：三个数据源需要统一治理。
画面文字：
1.{i} 研究背景
三个数据源需要统一治理。
```
''' for i in range(1, 4))

    def test_accepts_all_supported_themes(self):
        for theme in ('blue', 'green', 'red'):
            self.assertEqual([], self.check.validate(self.document(theme), theme))

    def test_rejects_replaced_prefix_on_one_slide(self):
        text = self.document().replace(self.check.style_prefix('blue'), '白底蓝橙，少图标、多色块。', 1)
        self.assertTrue(self.check.validate(text))

    def test_rejects_duplicate_page_numbers(self):
        self.assertTrue(self.check.validate(self.document().replace('P02｜', 'P01｜')))

    def test_rejects_missing_layout_and_content_number(self):
        text = self.document().replace('版式：顶栏占高9%，下方结论，两列证据，右图占主体55%。', '')
        text = text.replace('1.1 研究背景', '研究背景')
        self.assertTrue(self.check.validate(text))

    def test_rejects_all_light_headers(self):
        text = self.document().replace('标题系统：全宽顶部标题条', '标题系统：左上编号锚点')
        self.assertTrue(self.check.validate(text))

    def test_rejects_theme_drift(self):
        self.assertTrue(self.check.validate(self.document('green'), 'blue'))


if __name__ == '__main__':
    unittest.main()
