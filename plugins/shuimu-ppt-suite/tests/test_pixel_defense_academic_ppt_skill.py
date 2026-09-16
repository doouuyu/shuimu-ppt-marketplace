import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "pixel-defense-academic-ppt"


class PixelDefenseAcademicPptSkillContractTest(unittest.TestCase):
    def test_skill_declares_normalized_name(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: pixel-defense-academic-ppt", text)

    def test_ui_uses_chinese_style_name(self):
        text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "像素答辩学术汇报风"', text)

    def test_skill_reuses_base_image_deck_workflow(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../ppt-image-deck/SKILL.md", text)

    def test_style_contract_captures_stable_layout_language(self):
        text = (SKILL_ROOT / "references" / "style-contract.md").read_text(encoding="utf-8")
        required = (
            "白底",
            "顶部标题条",
            "层级编号",
            "左侧竖向提纲",
            "红色重点",
            "底部结论条",
            "蓝色",
            "绿色",
            "红色",
        )
        self.assertTrue(all(term in text for term in required))

    def test_reference_material_is_visual_evidence_only(self):
        text = (SKILL_ROOT / "references" / "style-contract.md").read_text(encoding="utf-8")
        required = (
            "用户材料是唯一内容来源",
            "不得复制",
            "像素答辩 Logo",
            "视频播放控件",
            "示例人物",
        )
        self.assertTrue(all(term in text for term in required))

    def test_source_inventory_records_both_pdfs_and_full_review_scope(self):
        text = (SKILL_ROOT / "references" / "source-inventory.md").read_text(encoding="utf-8")
        required = (
            "像素答辩_1-500.pdf",
            "像素答辩_501-1000.pdf",
            "df6dc376c502314cc0efa06f35e03d1582ead93f7b468b7548d24eb178527241",
            "28b816ac658900e4455b29a922c126a9478232cacb10dae20654269c199eb773",
            "全部 1000 页",
            "500 + 500",
            "无文本层",
        )
        self.assertTrue(all(term in text for term in required))

    def test_skill_loads_page_family_map_before_prompting(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/page-family-map.md", text)
        self.assertIn("先判定叙事类型", text)
        self.assertIn("再为每页选择页面家族", text)

    def test_page_family_map_covers_full_reference_grammar(self):
        text = (SKILL_ROOT / "references" / "page-family-map.md").read_text(encoding="utf-8")
        required = (
            "页面家族选择矩阵",
            "三种封面",
            "四种提纲",
            "全宽顶部标题条",
            "垂直侧栏",
            "证据图版",
            "顶部结论句",
            "人才/基金答辩",
            "科技奖励/项目申报",
            "重点实验室建设",
        )
        self.assertTrue(all(term in text for term in required))

    def test_style_contract_has_density_and_typography_rules(self):
        text = (SKILL_ROOT / "references" / "style-contract.md").read_text(encoding="utf-8")
        required = (
            "密度三级",
            "封面宋体感",
            "正文黑体",
            "结构化证据矩阵",
            "红色强调",
            "结论先行",
            "不得生成微小伪文字",
        )
        self.assertTrue(all(term in text for term in required))

    def test_compact_visual_overview_is_retained(self):
        overview = SKILL_ROOT / "assets" / "style-reference-overview.png"
        self.assertTrue(overview.is_file())
        self.assertGreater(overview.stat().st_size, 10_000)

    def test_content_layout_reference_is_retained(self):
        overview = SKILL_ROOT / "assets" / "content-layout-reference.png"
        self.assertTrue(overview.is_file())
        self.assertGreater(overview.stat().st_size, 10_000)

    def test_router_selects_specialized_skill_before_generic_image_deck(self):
        text = (PLUGIN_ROOT / "skills" / "shuimu-ppt" / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(text.index("$pixel-defense-academic-ppt"), text.index("$ppt-image-deck"))

    def test_plugin_manifest_lists_nine_workflows_and_new_style(self):
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn("九种水木 PPT 工作流", manifest["interface"]["shortDescription"])
        self.assertIn("像素答辩学术汇报风", manifest["interface"]["longDescription"])


if __name__ == "__main__":
    unittest.main()
