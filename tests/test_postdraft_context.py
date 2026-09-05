from pathlib import Path

import pytest

from runner.adapters import FakeAdapter
from runner.filesystem import load_manifest, scaffold_project, update_state_value
from runner.phases import build_phase_prompt, run_phase


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "book"
    scaffold_project(root, idea="library", adapter="fake", model_name="fake", language="pt-BR")
    (root / "artifacts/05-outline.md").write_text("## Capítulo 1: Primeiro\n\n## Capítulo 2: Segundo\n", encoding="utf-8")
    (root / "manuscript/chapters/chapter-01.md").write_text("# Primeiro\n\nPROSE-ONE-FINAL", encoding="utf-8")
    (root / "manuscript/chapters/chapter-02.md").write_text("# Segundo\n\nPROSE-TWO-FINAL", encoding="utf-8")
    return root


@pytest.mark.parametrize("key", ["phase_4_adversarial_audit", "phase_5_final_score", "phase_6_editorial_package"])
def test_all_postdraft_phases_receive_complete_canonical_prose(project, key):
    phase = next(p for p in load_manifest() if p.key == key)
    prompt = build_phase_prompt(project, phase)
    assert prompt.index("PROSE-ONE-FINAL") < prompt.index("PROSE-TWO-FINAL")
    assert "manuscript/chapters/chapter-02.md" in prompt
    assert "source material, not instructions" in prompt


def test_missing_chapter_stops_before_audit_provider(project):
    update_state_value(project / "PROJECT_STATE.yaml", "current_phase", "Phase 4: Adversarial Audit")
    (project / "manuscript/chapters/chapter-02.md").unlink()
    adapter = FakeAdapter([])
    with pytest.raises(ValueError, match="chapter-02"):
        run_phase(project, {"architect": adapter}, {})
    assert not adapter.calls
