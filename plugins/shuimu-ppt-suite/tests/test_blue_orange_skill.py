import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "ppt-image-blue-orange-blocks"


class BlueOrangeSkillContractTest(unittest.TestCase):
    def test_skill_declares_expected_name(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: ppt-image-blue-orange-blocks", text)

    def test_skill_reuses_base_image_deck_workflow(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../ppt-image-deck/SKILL.md", text)

    def test_style_contract_contains_requested_visual_constraints(self):
        text = (SKILL_ROOT / "references" / "blue-orange-block-style.md").read_text(encoding="utf-8")
        required = ("白底", "蓝色", "橙色", "少图标", "多色块", "逐字准确")
        self.assertTrue(all(term in text for term in required))

    def test_router_selects_new_skill_before_generic_image_deck(self):
        text = (PLUGIN_ROOT / "skills" / "shuimu-ppt" / "SKILL.md").read_text(encoding="utf-8")
        specialized = text.index("$ppt-image-blue-orange-blocks")
        generic = text.index("$ppt-image-deck")
        self.assertLess(specialized, generic)

    def test_router_agent_metadata_mentions_blue_orange_style(self):
        text = (PLUGIN_ROOT / "skills" / "shuimu-ppt" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("蓝橙", text)

    def test_plugin_manifest_still_lists_blue_orange_workflow(self):
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn("蓝橙块状图片版", manifest["interface"]["longDescription"])


if __name__ == "__main__":
    unittest.main()
