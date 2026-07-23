from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.distribution import (  # type: ignore  # noqa: E402
    BACKUP_DIRECTORY,
    INSTALL_RECORD,
    install_suite,
    resolve_install_root,
    selected_skills,
    validate_suite,
)


class DistributionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-distribution-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_portable_suite_contract_is_valid(self) -> None:
        result = validate_suite()
        self.assertTrue(result["ok"], msg="\n".join(result["errors"]))

    def test_runtime_paths_are_resolved_without_platform_writes(self) -> None:
        fake_home = self.tempdir / "home"
        self.assertEqual(
            (fake_home / ".claude" / "skills").resolve(),
            resolve_install_root("claude", home=fake_home, environ={}),
        )
        self.assertEqual(
            (fake_home / ".codex" / "skills").resolve(),
            resolve_install_root("codex", home=fake_home, environ={}),
        )
        self.assertEqual(
            (fake_home / ".kimi-code" / "skills").resolve(),
            resolve_install_root("kimi", home=fake_home, environ={}),
        )
        custom_kimi_home = self.tempdir / "custom-kimi"
        self.assertEqual(
            (custom_kimi_home / "skills").resolve(),
            resolve_install_root(
                "kimi",
                home=fake_home,
                environ={"KIMI_CODE_HOME": str(custom_kimi_home)},
            ),
        )
        self.assertEqual(
            (fake_home / ".agents" / "skills").resolve(),
            resolve_install_root("shared", home=fake_home, environ={}),
        )

    def test_dry_run_does_not_create_destination(self) -> None:
        destination = self.tempdir / "dry-run-skills"
        result = install_suite("codex", destination=destination, dry_run=True)
        self.assertTrue(result["ok"])
        self.assertFalse(destination.exists())
        self.assertTrue(any(item["action"] == "install" for item in result["actions"]))

    def test_destination_file_fails_even_in_dry_run(self) -> None:
        destination = self.tempdir / "not-a-directory"
        destination.write_text("occupied\n", encoding="utf-8")
        result = install_suite("codex", destination=destination, dry_run=True)
        self.assertFalse(result["ok"])
        self.assertIn("not a directory", result["errors"][0])

    def test_install_copies_same_portable_suite_for_every_runtime(self) -> None:
        expected = set(selected_skills())
        for target in ("claude", "codex", "kimi"):
            destination = self.tempdir / target / "skills"
            result = install_suite(target, destination=destination)
            self.assertTrue(result["ok"], msg=str(result["errors"]))
            installed = {path.name for path in destination.iterdir() if path.is_dir() and not path.name.startswith(".")}
            self.assertEqual(expected, installed)
            self.assertTrue((destination / "book-genesis" / "SKILL.md").exists())
            self.assertFalse((destination / "book-genesis-codex").exists())
            self.assertTrue((destination / INSTALL_RECORD).exists())

    def test_legacy_profile_is_explicit(self) -> None:
        destination = self.tempdir / "legacy-dry-run"
        result = install_suite("claude", destination=destination, include_legacy=True, dry_run=True)
        actions = {item["skill"] for item in result["actions"]}
        self.assertIn("book-genesis-codex", actions)
        self.assertIn("book-genesis-full", actions)
        legacy_actions = result["legacy_actions"]
        self.assertTrue(any(item["component"] == "agents" for item in legacy_actions))
        self.assertTrue(any(item["component"] == "knowledge" for item in legacy_actions))

    def test_legacy_claude_profile_installs_native_agents_only_for_claude(self) -> None:
        claude_skills = self.tempdir / "claude" / "skills"
        result = install_suite("claude", destination=claude_skills, include_legacy=True)
        self.assertTrue(result["ok"], msg=str(result["errors"]))
        self.assertTrue((self.tempdir / "claude" / "agents" / "book-orchestrator.md").exists())
        self.assertTrue((self.tempdir / "claude" / "knowledge" / "bestseller-dna.md").exists())

        codex_skills = self.tempdir / "codex" / "skills"
        codex_result = install_suite("codex", destination=codex_skills, include_legacy=True)
        self.assertTrue(codex_result["ok"], msg=str(codex_result["errors"]))
        self.assertEqual([], codex_result["legacy_actions"])
        self.assertFalse((self.tempdir / "codex" / "agents").exists())

    def test_legacy_agent_conflict_is_backed_up_on_force(self) -> None:
        claude_skills = self.tempdir / "claude" / "skills"
        install_suite("claude", destination=claude_skills, include_legacy=True)
        agent_file = self.tempdir / "claude" / "agents" / "book-orchestrator.md"
        agent_file.write_text(agent_file.read_text(encoding="utf-8") + "\nlocal agent change\n", encoding="utf-8")

        blocked = install_suite("claude", destination=claude_skills, include_legacy=True)
        self.assertFalse(blocked["ok"])
        self.assertIn("agents/book-orchestrator.md", blocked["conflicts"])
        self.assertIn("local agent change", agent_file.read_text(encoding="utf-8"))

        replaced = install_suite("claude", destination=claude_skills, include_legacy=True, force=True)
        self.assertTrue(replaced["ok"], msg=str(replaced["errors"]))
        self.assertNotIn("local agent change", agent_file.read_text(encoding="utf-8"))
        backups = list(
            (claude_skills / BACKUP_DIRECTORY).glob("*/agents/book-orchestrator.md")
        )
        self.assertEqual(1, len(backups))
        self.assertIn("local agent change", backups[0].read_text(encoding="utf-8"))

    def test_conflict_requires_force(self) -> None:
        destination = self.tempdir / "skills"
        first = install_suite("codex", destination=destination)
        self.assertTrue(first["ok"])
        skill_file = destination / "book-genesis" / "SKILL.md"
        skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\nlocal change\n", encoding="utf-8")

        second = install_suite("codex", destination=destination)
        self.assertFalse(second["ok"])
        self.assertIn("book-genesis", second["conflicts"])
        self.assertIn("local change", skill_file.read_text(encoding="utf-8"))

    def test_force_backs_up_then_replaces_conflict(self) -> None:
        destination = self.tempdir / "skills"
        install_suite("kimi", destination=destination)
        skill_file = destination / "book-genesis" / "SKILL.md"
        skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\nlocal change\n", encoding="utf-8")

        result = install_suite("kimi", destination=destination, force=True)
        self.assertTrue(result["ok"], msg=str(result["errors"]))
        self.assertNotIn("local change", skill_file.read_text(encoding="utf-8"))
        backup_root = destination / BACKUP_DIRECTORY
        backups = list(backup_root.glob("*/book-genesis/SKILL.md"))
        self.assertEqual(1, len(backups))
        self.assertIn("local change", backups[0].read_text(encoding="utf-8"))

    def test_cli_verifies_suite(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "runner" / "cli.py"), "verify-suite"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
        self.assertIn("validation ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
