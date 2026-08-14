import hashlib
import json
import unittest
import zipfile
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "aihia"
REFERENCE = SKILL_ROOT / "assets" / "reference.pptx"
EXPECTED_REFERENCE_SHA256 = "ddddf2f5ea374d294654d8dc6cc908aaba7ac49c2d13e518b86f35cad72ce972"


class AihiaSkillContractTest(unittest.TestCase):
    def test_skill_declares_exact_requested_name(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: aihia", text)

    def test_retained_reference_is_exact_source_copy(self):
        digest = hashlib.sha256(REFERENCE.read_bytes()).hexdigest()
        self.assertEqual(EXPECTED_REFERENCE_SHA256, digest)

    def test_reference_contains_native_cover_source(self):
        with zipfile.ZipFile(REFERENCE) as deck:
            slide_xml = deck.read("ppt/slides/slide1.xml").decode("utf-8")
        self.assertIn("超级AI医院运营方案", slide_xml)

    def test_reference_contains_native_header_source(self):
        with zipfile.ZipFile(REFERENCE) as deck:
            slide_xml = deck.read("ppt/slides/slide6.xml").decode("utf-8")
        required = ('name="AutoShape 19"', 'name="AutoShape 20"', 'name="Picture 21"')
        self.assertTrue(all(marker in slide_xml for marker in required))

    def test_builder_supports_native_cover_and_content_roles(self):
        text = (SKILL_ROOT / "scripts" / "build_aihia_deck.mjs").read_text(encoding="utf-8")
        self.assertTrue('role === "cover"' in text and 'role === "content"' in text)

    def test_cover_builder_keeps_only_the_visible_native_field_set(self):
        text = (SKILL_ROOT / "scripts" / "build_aihia_deck.mjs").read_text(encoding="utf-8")
        required = (
            'shape.name === "AutoShape 8"',
            'shape.name === "AutoShape 9"',
            'shape.name === "AutoShape 10"',
            'image.name === "Picture 6"',
            'image.name === "Picture 7"',
        )
        self.assertTrue(all(marker in text for marker in required))

    def test_style_guide_records_template_palette_and_safe_area(self):
        text = (SKILL_ROOT / "references" / "template-guide.md").read_text(encoding="utf-8")
        required = ("#694CD5", "#6F34A7", "顶部 0—240 px", "第 1 页", "第 6 页")
        self.assertTrue(all(term in text for term in required))

    def test_router_selects_aihia_before_generic_image_deck(self):
        text = (PLUGIN_ROOT / "skills" / "shuimu-ppt" / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(text.index("$aihia"), text.index("$ppt-image-deck"))

    def test_plugin_manifest_lists_six_workflows(self):
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn("六种水木 PPT 工作流", manifest["interface"]["shortDescription"])


if __name__ == "__main__":
    unittest.main()
