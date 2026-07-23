from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.filesystem import (  # type: ignore  # noqa: E402
    advance_phase,
    create_demo,
    fill_outputs_for_demo,
    load_agent_registry,
    load_manifest,
    load_state_summary,
    prepare_agent_packet,
    prepare_phase,
    prepare_swarm_run,
    scaffold_project,
    validate_project,
)


class RunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-runner-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_manifest_loads_universal_pipeline(self) -> None:
        phases = load_manifest()
        self.assertEqual("Phase 0: Intake", phases[0].label)
        self.assertEqual("Phase 7: Editorial Package", phases[-1].label)
        self.assertEqual(8, len(phases))
        self.assertEqual("Phase 5: Literary Barrier Revision Loop", phases[5].label)

    def test_market_level_skills_are_packaged(self) -> None:
        bestseller = REPO_ROOT / "skills" / "book-bestseller-studio" / "SKILL.md"
        swarm = REPO_ROOT / "skills" / "book-swarm-panel" / "SKILL.md"
        self.assertTrue(bestseller.exists())
        self.assertTrue(swarm.exists())
        self.assertIn("canonical `book-genesis`", bestseller.read_text(encoding="utf-8"))
        self.assertIn("MiroFish", swarm.read_text(encoding="utf-8"))

    def test_agent_registry_loads_bestseller_team(self) -> None:
        agents = load_agent_registry()
        keys = {agent.key for agent in agents}
        self.assertIn("worldbuilder", keys)
        self.assertIn("prose_writer", keys)
        self.assertIn("pacing_engineer", keys)
        self.assertIn("viral_framing_strategist", keys)
        self.assertIn("scorekeeper", keys)
        self.assertIn("blind_literary_critic", keys)
        self.assertGreaterEqual(len(agents), 12)

    def test_init_creates_project_contract(self) -> None:
        scaffold_project(
            self.tempdir,
            idea="a detective audits a haunted manuscript",
            adapter="codex",
            model_name="gpt-5.5",
            language="en",
        )
        self.assertTrue((self.tempdir / "PROJECT_STATE.yaml").exists())
        self.assertTrue((self.tempdir / "ASSUMPTIONS.md").exists())
        self.assertTrue((self.tempdir / "RUN_REPORT.md").exists())
        self.assertTrue((self.tempdir / "artifacts" / "00-brief.md").exists())
        self.assertTrue((self.tempdir / "manuscript" / "chapters").is_dir())
        self.assertTrue((self.tempdir / "evaluations").is_dir())
        self.assertTrue((self.tempdir / "delivery").is_dir())
        summary = load_state_summary(self.tempdir)
        self.assertEqual("codex", summary["adapter"])
        self.assertEqual("Phase 0: Intake", summary["current_phase"])
        state = (self.tempdir / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
        self.assertIn("target_floor_words: 0", state)
        self.assertIn('length_gate: "pending"', state)

    def test_validate_checks_required_files(self) -> None:
        scaffold_project(self.tempdir, idea="", adapter="codex", model_name="gpt-5.5")
        result = validate_project(self.tempdir)
        self.assertTrue(result["ok"])
        self.assertEqual([], result["missing"])

    def test_prepare_phase_embeds_prompt_packet(self) -> None:
        scaffold_project(self.tempdir, idea="", adapter="codex", model_name="gpt-5.5")
        packet_path = prepare_phase(self.tempdir)
        packet = packet_path.read_text(encoding="utf-8")
        self.assertIn("Phase 0: Intake", packet)
        self.assertIn("references/prompts/intake.md", packet)
        self.assertIn("ASSUMPTIONS.md", packet)
        self.assertIn("Phase Prompt", packet)

    def test_literary_phase_packet_embeds_evaluator_protocol(self) -> None:
        scaffold_project(self.tempdir, idea="", adapter="codex", model_name="gpt-5.5")
        for phase in load_manifest()[:5]:
            fill_outputs_for_demo(self.tempdir, phase)
            result = advance_phase(self.tempdir)
            self.assertTrue(result["ok"])
        packet = prepare_phase(self.tempdir).read_text(encoding="utf-8")
        self.assertIn("Phase 5: Literary Barrier Revision Loop", packet)
        self.assertIn("Required Reference: references/scoring/evaluator-protocol.md", packet)
        self.assertIn("Independence Grades", packet)

    def test_prepare_swarm_run_creates_mirofish_bridge_contract(self) -> None:
        scaffold_project(self.tempdir, idea="", adapter="codex", model_name="gpt-5.5")
        chapters = self.tempdir / "manuscript" / "chapters"
        (chapters / "chapter-01.md").write_text("# Chapter 1\n\nText.\n", encoding="utf-8")
        run_dir = prepare_swarm_run(
            self.tempdir,
            slug="Launch Reaction",
            mode="public-opinion",
            run_date="2026-05-10",
        )
        self.assertEqual("2026-05-10-launch-reaction", run_dir.name)
        self.assertTrue((run_dir / "persona-roster.json").exists())
        self.assertTrue((run_dir / "mirofish-requirement.md").exists())
        sample_map = (run_dir / "sample-map.md").read_text(encoding="utf-8")
        self.assertIn("manuscript/chapters/chapter-01.md", sample_map)
        self.assertIn("public-opinion", sample_map)

    def test_prepare_agent_packet_creates_specialist_contract(self) -> None:
        scaffold_project(self.tempdir, idea="", adapter="codex", model_name="gpt-5.5")
        packet_path = prepare_agent_packet(self.tempdir, "pacing_engineer")
        packet = packet_path.read_text(encoding="utf-8")
        self.assertIn("Agent Packet: Pacing Engineer", packet)
        self.assertIn("8.5 pacing/opening target", packet)
        self.assertIn("artifacts/05-outline.md", packet)
        self.assertIn("skills/prose-craft/SKILL.md", packet)

    def test_blind_critic_packet_hides_threshold(self) -> None:
        scaffold_project(self.tempdir, idea="", adapter="codex", model_name="gpt-5.5")
        packet = prepare_agent_packet(self.tempdir, "blind_literary_critic").read_text(encoding="utf-8")
        self.assertIn("Blind evaluation: yes", packet)
        self.assertIn("Score floor: withheld from blind evaluator", packet)
        self.assertNotIn("8.5", packet)
        self.assertIn("previous scores", packet)

    def test_advance_blocks_unfilled_templates(self) -> None:
        scaffold_project(self.tempdir, idea="seed idea", adapter="codex", model_name="gpt-5.5")
        result = advance_phase(self.tempdir)
        self.assertFalse(result["ok"])
        self.assertIn("ASSUMPTIONS.md", result["pending"])
        self.assertIn("artifacts/00-brief.md", result["pending"])

    def test_advance_moves_after_phase_outputs_are_filled(self) -> None:
        scaffold_project(self.tempdir, idea="", adapter="codex", model_name="gpt-5.5")
        for relative in [
            "ASSUMPTIONS.md",
            "artifacts/00-brief.md",
            "artifacts/01-market-map.md",
            "artifacts/02-story-engine.md",
        ]:
            path = self.tempdir / relative
            path.write_text(f"# Filled {relative}\n\nReal content.\n", encoding="utf-8")
        result = advance_phase(self.tempdir)
        summary = load_state_summary(self.tempdir)
        self.assertTrue(result["ok"])
        self.assertEqual("Phase 1: Foundation", summary["current_phase"])

    def test_demo_runs_to_completion(self) -> None:
        create_demo(self.tempdir, adapter="codex", model_name="gpt-5.5")
        summary = load_state_summary(self.tempdir)
        self.assertEqual("completed", summary["status"])
        self.assertTrue((self.tempdir / "manuscript" / "chapters" / "chapter-01.md").exists())
        self.assertIn("mechanical demo", (self.tempdir / "RUN_REPORT.md").read_text(encoding="utf-8"))

    def test_independent_evaluator_protocol_is_packaged(self) -> None:
        protocol = (
            REPO_ROOT
            / "skills"
            / "book-genesis"
            / "references"
            / "scoring"
            / "evaluator-protocol.md"
        )
        self.assertTrue(protocol.exists())
        text = protocol.read_text(encoding="utf-8")
        self.assertIn("Independence Grades", text)
        self.assertIn("Grade C is diagnostic only", text)

    def test_cli_init_runs_by_path(self) -> None:
        project = self.tempdir / "cli-project"
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "runner" / "cli.py"),
                "init",
                str(project),
                "--idea",
                "a short test",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertTrue((project / "PROJECT_STATE.yaml").exists())


if __name__ == "__main__":
    unittest.main()
