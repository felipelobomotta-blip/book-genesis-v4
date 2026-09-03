from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.constants import load_genre_profile, load_model_map  # type: ignore  # noqa: E402


class GenreProfileTests(unittest.TestCase):
    def test_thriller_profile_matches_the_knowledge_base(self) -> None:
        profile = load_genre_profile("thriller")
        self.assertEqual("thriller", profile.key)
        self.assertEqual((1500, 3500), (profile.words_per_chapter_min, profile.words_per_chapter_max))
        self.assertEqual((30, 50), (profile.dialogue_min_pct, profile.dialogue_max_pct))
        self.assertEqual(3, profile.max_revision_cycles)
        self.assertTrue(profile.disruptor_default)

    def test_unknown_genre_falls_back_to_default(self) -> None:
        profile = load_genre_profile("cozy dinosaur western")
        self.assertEqual("default", profile.key)
        self.assertEqual((2000, 4500), (profile.words_per_chapter_min, profile.words_per_chapter_max))

    def test_aliases_and_case_resolve_to_a_profile(self) -> None:
        self.assertEqual("scifi", load_genre_profile("Science Fiction").key)
        self.assertEqual("literary", load_genre_profile("literary fiction").key)
        self.assertEqual("thriller", load_genre_profile("SUSPENSE").key)

    def test_nonfiction_does_not_get_the_disruptor_by_default(self) -> None:
        profile = load_genre_profile("nonfiction")
        self.assertFalse(profile.disruptor_default)
        self.assertEqual((0, 15), (profile.dialogue_min_pct, profile.dialogue_max_pct))


class ModelMapTests(unittest.TestCase):
    def test_every_role_has_an_adapter(self) -> None:
        model_map = load_model_map()
        for role in ("writer", "disruptor", "judge", "editor", "architect", "extractor"):
            self.assertIn(role, model_map)
            self.assertTrue(model_map[role].adapter, msg=f"{role} has no adapter")

    def test_judge_defaults_to_a_different_family_than_the_writer(self) -> None:
        model_map = load_model_map()
        self.assertNotEqual(model_map["writer"].adapter, model_map["judge"].adapter)


if __name__ == "__main__":
    unittest.main()
