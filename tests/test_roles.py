from pathlib import Path
import sys
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import AdapterError  # type: ignore  # noqa: E402
from runner.constants import ROLES  # type: ignore  # noqa: E402
from runner import roles  # type: ignore  # noqa: E402
from runner.roles import plan_roles  # type: ignore  # noqa: E402


class PlanRolesTests(unittest.TestCase):
    def test_wrapped_cli_requires_its_real_executable_not_just_python(self) -> None:
        with (
            patch.object(roles, "load_generic_adapters", return_value={"gemini": "python runner/bridge_gemini.py {model}", "muse-spark": "python runner/bridge_opencode.py {model}"}),
            patch.object(roles, "load_generic_adapter_requirements", return_value={"gemini": ["agy"], "muse-spark": ["opencode"]}),
            patch.object(roles.shutil, "which", side_effect=lambda name: "C:/Python/python.exe" if name == "python" else None),
        ):
            found = roles.available_adapters()
        self.assertFalse(found["gemini"])
        self.assertFalse(found["muse-spark"])

    def test_detection_parses_a_quoted_executable_path_with_spaces(self) -> None:
        template = '"C:\\Program Files\\Model Tool\\tool.exe" --stdio'
        with (
            patch.object(roles, "load_generic_adapters", return_value={"tool": template}),
            patch.object(roles, "load_generic_adapter_requirements", return_value={}),
            patch.object(roles.shutil, "which", side_effect=lambda name: r"C:\Program Files\Model Tool\tool.exe" if name.startswith("C:") else None),
        ):
            found = roles.available_adapters()
        self.assertTrue(found["tool"])
    def test_both_families_available_keeps_the_configured_map(self) -> None:
        plan = plan_roles(available={"claude": True, "codex": True})
        self.assertEqual("claude", plan.roles["writer"].adapter)
        self.assertEqual("codex", plan.roles["judge"].adapter)
        self.assertEqual([], plan.warnings)
        self.assertGreaterEqual(len(plan.panel), 2)

    def test_only_claude_moves_the_judge_to_claude_on_a_different_model_and_warns(self) -> None:
        plan = plan_roles(available={"claude": True, "codex": False})
        self.assertEqual("claude", plan.roles["judge"].adapter)
        self.assertNotEqual(plan.roles["writer"].model, plan.roles["judge"].model)
        self.assertTrue(any("single family" in warning.lower() for warning in plan.warnings), msg=plan.warnings)
        for member in plan.panel:
            self.assertEqual("claude", member.adapter)

    def test_only_codex_moves_every_role_to_codex(self) -> None:
        plan = plan_roles(available={"claude": False, "codex": True})
        for role in ROLES:
            self.assertEqual("codex", plan.roles[role].adapter, msg=role)
        self.assertTrue(any("single family" in warning.lower() for warning in plan.warnings))

    def test_nothing_available_names_what_to_install(self) -> None:
        with self.assertRaises(AdapterError) as context:
            plan_roles(available={"claude": False, "codex": False})
        message = str(context.exception)
        self.assertIn("claude", message)
        self.assertIn("codex", message)

    def test_panel_members_keep_distinct_personas(self) -> None:
        plan = plan_roles(available={"claude": True, "codex": True})
        personas = [member.persona for member in plan.panel]
        self.assertEqual(len(personas), len(set(personas)))
        self.assertTrue(all(persona for persona in personas))


if __name__ == "__main__":
    unittest.main()
