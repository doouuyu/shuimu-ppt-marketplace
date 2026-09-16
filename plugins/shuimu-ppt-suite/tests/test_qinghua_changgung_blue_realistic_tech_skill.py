import hashlib
import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "qinghua-changgung-blue-realistic-tech"
REFERENCE = SKILL_ROOT / "assets" / "style-reference.jpg"
EXPECTED_REFERENCE_SHA256 = "17e826b0fc167d9f9b651b80018f35b4e759a5e74f522fb8408ee94f4febd9c0"


class QinghuaChanggungBlueRealisticTechSkillContractTest(unittest.TestCase):
    def test_skill_declares_normalized_name(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: qinghua-changgung-blue-realistic-tech", text)

    def test_ui_uses_requested_chinese_name(self):
        text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "清华长庚蓝写实科技风"', text)

    def test_skill_reuses_base_image_deck_workflow(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../ppt-image-deck/SKILL.md", text)

    def test_retained_visual_reference_is_exact_copy(self):
        digest = hashlib.sha256(REFERENCE.read_bytes()).hexdigest()
        self.assertEqual(EXPECTED_REFERENCE_SHA256, digest)

    def test_style_contract_records_distinctive_visual_system(self):
        text = (SKILL_ROOT / "references" / "style-contract.md").read_text(encoding="utf-8")
        required = (
            "冰白",
            "深海军蓝",
            "亮蓝",
            "青蓝",
            "橙色",
            "顶部短竖线",
            "横向细线",
            "写实医疗场景",
            "软件界面",
            "底部蓝色流线",
        )
        self.assertTrue(all(term in text for term in required))

    def test_reference_copy_is_never_a_content_source(self):
        text = (SKILL_ROOT / "references" / "style-contract.md").read_text(encoding="utf-8")
        required = ("不得复制", "参考图中的文字", "用户材料是唯一内容来源")
        self.assertTrue(all(term in text for term in required))

    def test_router_selects_specialized_skill_before_generic_image_deck(self):
        text = (PLUGIN_ROOT / "skills" / "shuimu-ppt" / "SKILL.md").read_text(encoding="utf-8")
        specialized = text.index("$qinghua-changgung-blue-realistic-tech")
        generic = text.index("$ppt-image-deck")
        self.assertLess(specialized, generic)

    def test_plugin_manifest_lists_nine_workflows_and_new_style(self):
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn("九种水木 PPT 工作流", manifest["interface"]["shortDescription"])
        self.assertIn("清华长庚蓝写实科技风", manifest["interface"]["longDescription"])


if __name__ == "__main__":
    unittest.main()
