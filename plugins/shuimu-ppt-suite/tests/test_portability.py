import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]


class PluginPortabilityTest(unittest.TestCase):
    def test_image_deck_builder_is_resolved_from_current_skill(self):
        text = (PLUGIN_ROOT / "skills" / "ppt-image-deck" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('python "$SKILL_DIR/scripts/build_pptx.py"', text)
        self.assertNotIn('${CODEX_HOME:-$HOME/.codex}/skills/ppt-image-deck', text)

    def test_repo_marketplace_points_to_packaged_plugin(self):
        marketplace = json.loads(
            (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        entry = marketplace["plugins"][0]
        self.assertEqual("shuimu-ppt-suite", entry["name"])
        self.assertEqual("./plugins/shuimu-ppt-suite", entry["source"]["path"])
        self.assertTrue((REPO_ROOT / entry["source"]["path"]).is_dir())


if __name__ == "__main__":
    unittest.main()
