"""The `book-genesis` entry point (ADR 0009).

`new` and `resume` (and the bare command on a terminal) open the guided session: one idea in,
the person watching and agreeing along the way, a judged manuscript with its score out.
Every other command is the command layer in ``runner.cli``, unchanged.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List, Optional

from runner import cli
from runner.adapters import AdapterError
from runner.export import export_project
from runner.filesystem import scaffold_project
from runner.review import build_review
from runner.roles import available_adapters, build_role_adapters
from runner.session import run_session
from runner.ui import make_view
from runner.userconfig import load_user_config

EXIT_CODES = {
    "completed": cli.EXIT_OK,
    "stopped": cli.EXIT_OK,
    "awaiting_human": cli.EXIT_AWAITING_HUMAN,
    "awaiting_manual": cli.EXIT_AWAITING_MANUAL,
    "blocked": cli.EXIT_BLOCKED,
    "failed": cli.EXIT_FAILURE,
}
SESSION_COMMANDS = ("new", "resume")
HELP_FLAGS = ("-h", "--help", "help")
OVERVIEW = """book-genesis - develop your idea with drafts, model feedback, and saved revisions.

  book-genesis setup            choose your providers and models. Once.
  book-genesis new              give it an idea; guide the writing and review process
  book-genesis resume <folder>  continue where you stopped
  book-genesis doctor           what will run where, and whether every key is set
  book-genesis review <folder>  read chapters and safe local version history in a browser
  book-genesis export <folder> --format markdown|epub  create a local canonical export

Useful flags on `new` and `resume`:
  --yes        never ask (also what happens with no terminal: a script, cron, CI)
  --plain      plain lines instead of the live interface
  --human      pause after chapter 1 until you have read it yourself
  --manual     no provider at all: paste every reply by hand
  --chapters N stop after N chapters instead of writing the whole book

One step at a time: brief, chapter, book, polish, judge, panel, run-phase, approve,
init, status, validate, demo. Run `book-genesis <command> --help` for any of them.
An audit that requests revision stops completion until the manuscript is revised.
"""


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["new"] if (load_user_config() is not None or any(available_adapters().values())) else ["setup"]
    if argv[0] in HELP_FLAGS:
        # argparse's own top-level help is a 19-command positional dump; the front door of an
        # open-source tool has to read like a sentence.
        cli._utf8_console()
        print(OVERVIEW, end="")
        return cli.EXIT_OK
    if argv[0] in SESSION_COMMANDS:
        cli._utf8_console()
        return session_main(argv)
    if argv[0] == "review":
        cli._utf8_console()
        return review_main(argv[1:])
    if argv[0] == "export":
        cli._utf8_console()
        return export_main(argv[1:])
    return cli.main(argv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="book-genesis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="From one idea to a judged manuscript, with you agreeing along the way")
    new_parser.add_argument("--idea", default="")
    new_parser.add_argument("--language", default="")
    new_parser.add_argument("--path", default="", help="Project folder (default: ./books/<slug>)")
    _shared(new_parser)

    resume_parser = subparsers.add_parser("resume", help="Continue a project from wherever it stopped")
    resume_parser.add_argument("path")
    _shared(resume_parser)
    return parser


def _shared(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--yes", action="store_true", help="Never ask: the fully autonomous run (also the default without a terminal)")
    parser.add_argument("--plain", action="store_true", help="Lines instead of the live interface")
    parser.add_argument("--human", action="store_true", help="Pause after chapter 1 until you approve it")
    parser.add_argument("--manual", action="store_true", help="No provider: paste every reply by hand")
    parser.add_argument("--chapters", type=int, default=None, help="Stop after this many chapters (a bounded test run)")
    parser.add_argument("--fake-responses", default="", help="Scripted responses for every role (tests)")


def session_main(argv: List[str], view=None) -> int:
    args = build_parser().parse_args(argv)
    view = view or make_view(plain=args.plain)
    if args.chapters is not None and args.chapters <= 0:
        view.fail("--chapters must be a positive integer.")
        return cli.EXIT_USAGE

    if args.command == "new":
        idea = args.idea.strip() or view.ask("What is the book about? One sentence is enough", "")
        if not idea:
            view.fail("An idea is required (use --idea or type it when asked).")
            return cli.EXIT_USAGE
        language = args.language.strip() or view.ask("Language", "en")
        project = Path(args.path) if args.path else Path("books") / cli._slug(idea)
        if (project / "PROJECT_STATE.yaml").exists():
            view.fail(f"A book already exists at {project}. Use `book-genesis resume` or choose a new --path.")
            return cli.EXIT_USAGE
        try:
            scaffold_project(project, idea=idea, language=language, adapter="auto", model_name="auto")
        except (OSError, ValueError) as exc:
            view.fail(f"Could not create the project: {exc}")
            return cli.EXIT_FAILURE
    else:
        project = Path(args.path)
        if not (project / "PROJECT_STATE.yaml").exists():
            view.fail(f"no project at {project}; run `book-genesis new` first")
            return cli.EXIT_FAILURE

    try:
        setup = build_setup(project, fake_responses=args.fake_responses, manual=args.manual)
    except AdapterError as exc:
        view.fail(str(exc))
        return cli.EXIT_FAILURE

    try:
        result = run_session(project, setup, view, yes=args.yes or not view.interactive, human=args.human, chapters=args.chapters)
    except OSError as exc:
        view.fail(f"Could not finish the file operation: {exc}. Continue with: book-genesis resume {project}")
        return cli.EXIT_FAILURE
    except KeyboardInterrupt:
        view.fail(f"\ninterrupted; continue any time with: book-genesis resume {project}")
        return cli.EXIT_FAILURE
    return EXIT_CODES.get(result.status, cli.EXIT_FAILURE)


def review_main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="book-genesis review", description="Create a local, self-contained reading and revision page.")
    parser.add_argument("project")
    parser.add_argument("--open", action="store_true", help="Open the generated local file in the default browser")
    args = parser.parse_args(argv)
    try:
        output = build_review(Path(args.project))
        print(f"review: {output}")
        if args.open:
            import webbrowser
            if not webbrowser.open(output.as_uri()):
                print(f"Could not open automatically; open this local file: {output}")
    except (OSError, ValueError) as exc:
        print(f"Review failed: {exc}")
        return cli.EXIT_FAILURE
    return cli.EXIT_OK


def export_main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="book-genesis export", description="Export canonical chapters locally; never uploads the manuscript.")
    parser.add_argument("project")
    parser.add_argument("--format", choices=("markdown", "epub"), required=True)
    parser.add_argument("--output", help="Destination file (default: project/exports/manuscript.<format>)")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing export file")
    args = parser.parse_args(argv)
    try:
        output = export_project(Path(args.project), args.format, Path(args.output) if args.output else None, args.overwrite)
        print(f"export: {output}")
    except (OSError, ValueError) as exc:
        print(f"Export failed: {exc}")
        return cli.EXIT_FAILURE
    return cli.EXIT_OK


def build_setup(project: Path, *, fake_responses: str = "", manual: bool = False):
    fake_path = Path(fake_responses) if fake_responses else None
    manual_dir = project / "work" / "manual" if manual else None
    user_config = None if fake_path is not None else load_user_config()
    return build_role_adapters(fake_responses_path=fake_path, manual_dir=manual_dir, user_config=user_config)


if __name__ == "__main__":
    raise SystemExit(main())
