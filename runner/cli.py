from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner.adapters import AdapterError  # noqa: E402
from runner.book import run_book  # noqa: E402
from runner.brief import TAIL_WORDS, build_chapter_brief, tail_words  # noqa: E402
from runner.chapter import AwaitingHuman, approve, clean_chapter, run_chapter  # noqa: E402
from runner.constants import load_model_map  # noqa: E402
from runner.filesystem import (  # noqa: E402
    advance_phase,
    create_demo,
    load_state_summary,
    prepare_agent_packet,
    prepare_phase,
    prepare_swarm_run,
    scaffold_project,
    validate_project,
)
from runner.judge import Verdict, judge_chapter  # noqa: E402
from runner.phases import run_phase  # noqa: E402
from runner.roles import build_adapter, build_role_adapters, load_fake_responses  # noqa: E402

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_AWAITING_HUMAN = 3
EXIT_BLOCKED = 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="book-genesis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a Book Genesis project tree")
    init_parser.add_argument("path")
    init_parser.add_argument("--idea", default="")
    init_parser.add_argument("--language", default="")
    init_parser.add_argument("--adapter", default="claude")
    init_parser.add_argument("--model", default="opus")
    init_parser.add_argument("--force", action="store_true")

    status_parser = subparsers.add_parser("status", help="Print project status")
    status_parser.add_argument("path")

    validate_parser = subparsers.add_parser("validate", help="Validate required project files")
    validate_parser.add_argument("path")

    prepare_parser = subparsers.add_parser("prepare-phase", help="Write work/current-phase.md")
    prepare_parser.add_argument("path")

    advance_parser = subparsers.add_parser("advance-phase", help="Advance after required outputs exist")
    advance_parser.add_argument("path")

    swarm_parser = subparsers.add_parser("prepare-swarm", help="Create a book-swarm run folder")
    swarm_parser.add_argument("path")
    swarm_parser.add_argument("--slug", default="reader-swarm")
    swarm_parser.add_argument("--mode", default="hybrid")

    agent_parser = subparsers.add_parser("prepare-agent-packet", help="Create a specialist agent packet")
    agent_parser.add_argument("path")
    agent_parser.add_argument("agent")

    demo_parser = subparsers.add_parser("demo", help="Create a deterministic mechanical demo")
    demo_parser.add_argument("path")
    demo_parser.add_argument("--adapter", default="fake")
    demo_parser.add_argument("--model", default="fake")

    judge_parser = subparsers.add_parser("judge", help="Blind-read one chapter file and print the reader's verdict")
    judge_parser.add_argument("file")
    judge_parser.add_argument("--previous", default="", help="Previous chapter file; only its last words are shown to the reader")
    judge_parser.add_argument("--genre", default="")
    judge_parser.add_argument("--reader", default="")
    judge_parser.add_argument("--anchor", default="", help="Published chapter in the same genre, for comparison")
    judge_parser.add_argument("--adapter", default="", help="claude, codex, or fake (default: the judge role in models.yaml)")
    judge_parser.add_argument("--model", default="")
    judge_parser.add_argument("--fake-responses", default="")
    judge_parser.add_argument("--out", default="", help="Write the raw judge response here")

    brief_parser = subparsers.add_parser("brief", help="Assemble briefs/chapter-NN.md from the project files")
    brief_parser.add_argument("path")
    brief_parser.add_argument("chapter", type=int)

    chapter_parser = subparsers.add_parser("chapter", help="Write, disrupt, judge and revise one chapter")
    chapter_parser.add_argument("path")
    chapter_parser.add_argument("chapter", type=int)
    chapter_parser.add_argument("--fake-responses", default="", help="Scripted responses for every role (tests)")

    approve_parser = subparsers.add_parser("approve", help="Record that a human read a chapter and it holds up")
    approve_parser.add_argument("path")
    approve_parser.add_argument("slug", help="e.g. chapter-01")

    book_parser = subparsers.add_parser("book", help="Write every remaining chapter until done, blocked, or a human is needed")
    book_parser.add_argument("path")
    book_parser.add_argument("--from", dest="start", type=int, default=None)
    book_parser.add_argument("--to", dest="end", type=int, default=None)
    book_parser.add_argument("--fake-responses", default="", help="Scripted responses for every role (tests)")

    run_phase_parser = subparsers.add_parser("run-phase", help="Run the current phase through the model; advance when its outputs exist")
    run_phase_parser.add_argument("path")
    run_phase_parser.add_argument("--fake-responses", default="", help="Scripted responses (tests)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _utf8_console()
    target = Path(args.path) if hasattr(args, "path") else None

    if args.command == "init":
        scaffold_project(
            target,
            idea=args.idea,
            language=args.language,
            adapter=args.adapter,
            model_name=args.model,
            force=args.force,
        )
        print(f"Initialized project at {target}")
        return EXIT_OK

    if args.command == "status":
        summary = load_state_summary(target)
        print(f"title={summary['title']}")
        print(f"genre={summary['genre']}")
        print(f"adapter={summary['adapter']}")
        print(f"model_name={summary['model_name']}")
        print(f"current_phase={summary['current_phase']}")
        print(f"status={summary['status']}")
        return EXIT_OK

    if args.command == "validate":
        result = validate_project(target)
        if not result["ok"]:
            print("Validation failed")
            for item in result["missing"]:
                print(item)
            return EXIT_FAILURE
        print("Validation ok")
        return EXIT_OK

    if args.command == "prepare-phase":
        packet_path = prepare_phase(target)
        print(f"Prepared phase packet at {packet_path}")
        return EXIT_OK

    if args.command == "advance-phase":
        result = advance_phase(target)
        if not result["ok"]:
            print("Advance failed")
            for item in result["pending"]:
                print(item)
            return EXIT_FAILURE
        print(f"Advanced to {result['next_phase']}")
        return EXIT_OK

    if args.command == "prepare-swarm":
        run_dir = prepare_swarm_run(target, slug=args.slug, mode=args.mode)
        print(f"Prepared book-swarm run at {run_dir}")
        return EXIT_OK

    if args.command == "prepare-agent-packet":
        packet_path = prepare_agent_packet(target, args.agent)
        print(f"Prepared agent packet at {packet_path}")
        return EXIT_OK

    if args.command == "demo":
        create_demo(target, adapter=args.adapter, model_name=args.model)
        print(f"Created completed mechanical demo at {target}")
        return EXIT_OK

    if args.command == "judge":
        return _judge_command(args)

    if args.command == "brief":
        brief_path = target / "briefs" / f"chapter-{args.chapter:02d}.md"
        try:
            build_chapter_brief(target, args.chapter)
        except ValueError as exc:
            print(f"Brief failed: {exc}")
            return EXIT_FAILURE
        print(f"Wrote {brief_path}")
        return EXIT_OK

    if args.command == "chapter":
        return _chapter_command(args, target)

    if args.command == "approve":
        marker = approve(target, args.slug)
        print(f"Approved {args.slug}: {marker}")
        return EXIT_OK

    if args.command == "book":
        return _book_command(args, target)

    if args.command == "run-phase":
        return _run_phase_command(args, target)

    parser.error("Unknown command")
    return EXIT_USAGE


def _judge_command(args: argparse.Namespace) -> int:
    chapter_path = Path(args.file)
    prose = clean_chapter(chapter_path.read_text(encoding="utf-8"))
    previous_tail = ""
    if args.previous:
        previous_tail = tail_words(Path(args.previous).read_text(encoding="utf-8"), TAIL_WORDS)
    anchor = Path(args.anchor).read_text(encoding="utf-8") if args.anchor else None

    judge_role = load_model_map().get("judge")
    adapter_name = args.adapter or (judge_role.adapter if judge_role else "claude")
    model = args.model or (judge_role.model if judge_role and adapter_name == judge_role.adapter else "")
    fake_responses = load_fake_responses(Path(args.fake_responses)) if args.fake_responses else None
    try:
        adapter = build_adapter(adapter_name, fake_responses=fake_responses)
        verdict = judge_chapter(
            prose,
            previous_tail,
            args.genre,
            adapter,
            model,
            anchor=anchor,
            reader=args.reader,
        )
    except (AdapterError, ValueError) as exc:
        print(f"Judge failed: {exc}")
        return EXIT_FAILURE

    print(f"# {chapter_path.name} read blind by {adapter_name}{' ' + model if model else ''}")
    print(format_verdict(verdict))
    if args.out:
        Path(args.out).write_text(verdict.raw, encoding="utf-8")
        print(f"raw response written to {args.out}")
    return EXIT_OK


def _chapter_command(args: argparse.Namespace, target: Path) -> int:
    fake_path = Path(args.fake_responses) if args.fake_responses else None
    try:
        adapters, models = build_role_adapters(fake_responses_path=fake_path)
        result = run_chapter(target, args.chapter, adapters, models=models)
    except AwaitingHuman as exc:
        print(f"Awaiting a human reader: {exc}")
        return EXIT_AWAITING_HUMAN
    except (AdapterError, ValueError, FileNotFoundError) as exc:
        print(f"Chapter {args.chapter} failed: {exc}")
        return EXIT_FAILURE

    last = result.verdicts[-1] if result.verdicts else None
    print(f"chapter {args.chapter}: {result.status} after {result.cycles} revision cycle(s)")
    if last is not None:
        print(format_verdict(last))
    print(f"draft: {result.draft_path}")
    return EXIT_OK if result.accepted else EXIT_BLOCKED


def _book_command(args: argparse.Namespace, target: Path) -> int:
    fake_path = Path(args.fake_responses) if args.fake_responses else None
    try:
        adapters, models = build_role_adapters(fake_responses_path=fake_path)
        result = run_book(target, adapters, models, start=args.start, end=args.end)
    except (AdapterError, ValueError, FileNotFoundError) as exc:
        print(f"Book failed: {exc}")
        return EXIT_FAILURE

    print(f"book: {result.status} (chapters written this run: {result.chapters_done or 'none'})")
    print(result.message)
    if result.status == "awaiting_human":
        return EXIT_AWAITING_HUMAN
    if result.status == "blocked":
        return EXIT_BLOCKED
    return EXIT_OK


def _run_phase_command(args: argparse.Namespace, target: Path) -> int:
    fake_path = Path(args.fake_responses) if args.fake_responses else None
    try:
        adapters, models = build_role_adapters(fake_responses_path=fake_path)
        result = run_phase(target, adapters, models)
    except (AdapterError, ValueError, FileNotFoundError, KeyError) as exc:
        print(f"Phase failed: {exc}")
        return EXIT_FAILURE

    print(f"{result.phase}: wrote {', '.join(result.written) or 'nothing'}")
    if result.ignored:
        print(f"ignored blocks not required by this phase: {', '.join(result.ignored)}")
    if not result.ok:
        print("not advanced; still missing:")
        for item in result.pending:
            print(f"  - {item}")
        return EXIT_FAILURE
    print(f"next phase: {result.next_phase}")
    return EXIT_OK


def format_verdict(verdict: Verdict) -> str:
    remember = "\n".join(f"  - {item}" for item in verdict.remember) or "  (nothing)"
    flags = ", ".join(verdict.flags)
    return (
        f"turn_page: {'yes' if verdict.turn_page else 'no'}\n"
        f"stopped_at: {verdict.stopped_at}\n"
        f"remember:\n{remember}\n"
        f"flags: [{flags}]\n"
        f"vs_previous: {verdict.vs_previous}\n"
        f"vs_anchor: {verdict.vs_anchor}"
    )


def _utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


if __name__ == "__main__":
    raise SystemExit(main())
