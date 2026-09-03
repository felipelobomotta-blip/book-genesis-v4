from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner.adapters import AdapterError, AwaitingManual  # noqa: E402
from runner.book import run_book  # noqa: E402
from runner.brief import TAIL_WORDS, build_chapter_brief, tail_words  # noqa: E402
from runner.chapter import AwaitingHuman, approve, clean_chapter, run_chapter  # noqa: E402
from runner.constants import ROLES, load_model_map  # noqa: E402
from runner.filesystem import (  # noqa: E402
    advance_phase,
    create_demo,
    current_phase,
    load_state_summary,
    prepare_agent_packet,
    prepare_phase,
    prepare_swarm_run,
    scaffold_project,
    validate_project,
)
from runner.judge import Verdict, judge_chapter  # noqa: E402
from runner.phases import DRAFTING_LABEL, run_phase  # noqa: E402
from runner.roles import (  # noqa: E402
    KNOWN_CLIS,
    available_adapters,
    build_adapter,
    build_role_adapters,
    load_fake_responses,
    plan_roles,
)
from runner.setup import run_setup  # noqa: E402
from runner.userconfig import load_user_config  # noqa: E402

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_AWAITING_HUMAN = 3
EXIT_BLOCKED = 4
EXIT_AWAITING_MANUAL = 5


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
    judge_parser.add_argument("--adapter", default="", help="claude, codex, or fake (default: the judge role of the plan)")
    judge_parser.add_argument("--model", default="")
    judge_parser.add_argument("--fake-responses", default="")
    judge_parser.add_argument("--out", default="", help="Write the raw judge response here")

    brief_parser = subparsers.add_parser("brief", help="Assemble briefs/chapter-NN.md from the project files")
    brief_parser.add_argument("path")
    brief_parser.add_argument("chapter", type=int)

    chapter_parser = subparsers.add_parser("chapter", help="Write, disrupt, judge and revise one chapter")
    chapter_parser.add_argument("path")
    chapter_parser.add_argument("chapter", type=int)
    chapter_parser.add_argument("--human", action="store_true", help="Pause after chapter 1 until a human approves it")
    chapter_parser.add_argument("--manual", action="store_true", help="No CLI: write each prompt to work/manual/ and wait for a pasted reply")
    chapter_parser.add_argument("--fake-responses", default="", help="Scripted responses for every role (tests)")

    approve_parser = subparsers.add_parser("approve", help="Record that a human read a chapter and it holds up (human mode)")
    approve_parser.add_argument("path")
    approve_parser.add_argument("slug", help="e.g. chapter-01")

    book_parser = subparsers.add_parser("book", help="Write every remaining chapter; chapter 1 is judged by the reader panel")
    book_parser.add_argument("path")
    book_parser.add_argument("--from", dest="start", type=int, default=None)
    book_parser.add_argument("--to", dest="end", type=int, default=None)
    book_parser.add_argument("--human", action="store_true", help="Pause after chapter 1 until a human approves it")
    book_parser.add_argument("--manual", action="store_true", help="No CLI: write each prompt to work/manual/ and wait for a pasted reply")
    book_parser.add_argument("--fake-responses", default="", help="Scripted responses for every role (tests)")

    run_phase_parser = subparsers.add_parser("run-phase", help="Run the current phase through the model; advance when its outputs exist")
    run_phase_parser.add_argument("path")
    run_phase_parser.add_argument("--manual", action="store_true", help="No CLI: write the prompt to work/manual/ and wait for a pasted reply")
    run_phase_parser.add_argument("--fake-responses", default="", help="Scripted responses (tests)")

    panel_parser = subparsers.add_parser("panel", help="Read one written chapter with the whole blind reader panel")
    panel_parser.add_argument("path")
    panel_parser.add_argument("chapter", type=int)
    panel_parser.add_argument("--manual", action="store_true", help="No CLI: write each seat's prompt to work/manual/")
    panel_parser.add_argument("--fake-responses", default="")

    subparsers.add_parser("doctor", help="Show which providers are available and how roles will be assigned")

    setup_parser = subparsers.add_parser("setup", help="Choose providers, connect API keys, pick models (once)")
    setup_parser.add_argument("--path", default="", help="Config file (default: ~/.book-genesis/config.yaml)")

    new_parser = subparsers.add_parser("new", help="From one idea to a judged manuscript and editorial package")
    new_parser.add_argument("--idea", default="")
    new_parser.add_argument("--language", default="")
    new_parser.add_argument("--path", default="", help="Project folder (default: ./books/<slug>)")
    new_parser.add_argument("--human", action="store_true", help="Pause after chapter 1 until you approve it")
    new_parser.add_argument("--manual", action="store_true", help="No provider: paste every reply by hand")
    new_parser.add_argument("--fake-responses", default="")

    resume_parser = subparsers.add_parser("resume", help="Continue a project from wherever it stopped")
    resume_parser.add_argument("path")
    resume_parser.add_argument("--human", action="store_true")
    resume_parser.add_argument("--manual", action="store_true")
    resume_parser.add_argument("--fake-responses", default="")

    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        argv = ["new"] if (load_user_config() is not None or any(available_adapters().values())) else ["setup"]
    parser = build_parser()
    args = parser.parse_args(argv)
    _utf8_console()
    target = Path(args.path) if getattr(args, "path", "") else None

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

    if args.command == "panel":
        return _panel_command(args, target)

    if args.command == "doctor":
        return _doctor_command()

    if args.command == "setup":
        return _setup_command(args)

    if args.command == "new":
        return _new_command(args)

    if args.command == "resume":
        return _drive(args, target)

    parser.error("Unknown command")
    return EXIT_USAGE


def _judge_command(args: argparse.Namespace) -> int:
    chapter_path = Path(args.file)
    prose = clean_chapter(chapter_path.read_text(encoding="utf-8"))
    previous_tail = ""
    if args.previous:
        previous_tail = tail_words(Path(args.previous).read_text(encoding="utf-8"), TAIL_WORDS)
    anchor = Path(args.anchor).read_text(encoding="utf-8") if args.anchor else None

    fake_responses = load_fake_responses(Path(args.fake_responses)) if args.fake_responses else None
    user_config = None if fake_responses is not None else load_user_config()
    adapter_name = args.adapter
    model = args.model
    try:
        if not adapter_name:
            plan = plan_roles(user_config=user_config)
            adapter_name = plan.roles["judge"].adapter
            model = model or plan.roles["judge"].model
        adapter = build_adapter(adapter_name, fake_responses=fake_responses, user_config=user_config)
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


def _setup(args: argparse.Namespace, target: Path | None = None):
    fake_path = Path(args.fake_responses) if getattr(args, "fake_responses", "") else None
    manual_dir = None
    if target is not None and getattr(args, "manual", False):
        manual_dir = target / "work" / "manual"
    user_config = None if fake_path is not None else load_user_config()
    setup = build_role_adapters(fake_responses_path=fake_path, manual_dir=manual_dir, user_config=user_config)
    for warning in setup.warnings:
        print(f"warning: {warning}")
    return setup


def _progress(message: str) -> None:
    print(message, flush=True)


def _setup_command(args: argparse.Namespace) -> int:
    import getpass

    def ask(prompt: str, default: str = "") -> str:
        shown = f"{prompt} [{default}]: " if default else f"{prompt}: "
        try:
            answer = input(shown).strip()
        except EOFError:
            answer = ""
        return answer or default

    def secret(prompt: str) -> str:
        try:
            return getpass.getpass(f"{prompt}: ").strip()
        except EOFError:
            return ""

    path = Path(args.path) if args.path else None
    run_setup(ask=ask, secret=secret, say=print, path=path)
    return EXIT_OK


def _new_command(args: argparse.Namespace) -> int:
    idea = args.idea.strip()
    if not idea:
        try:
            idea = input("Your idea, in one sentence: ").strip()
        except EOFError:
            idea = ""
    if not idea:
        print("An idea is required (use --idea or type it when asked).")
        return EXIT_USAGE
    language = args.language.strip()
    if not language:
        try:
            language = input("Language [en]: ").strip() or "en"
        except EOFError:
            language = "en"
    project = Path(args.path) if args.path else Path("books") / _slug(idea)
    if not (project / "PROJECT_STATE.yaml").exists():
        scaffold_project(project, idea=idea, language=language, adapter="auto", model_name="auto")
        print(f"project created at {project}", flush=True)
    return _drive(args, project)


def _drive(args: argparse.Namespace, project: Path) -> int:
    """Everything from the current phase to the editorial package, with progress on screen."""
    if project is None or not (project / "PROJECT_STATE.yaml").exists():
        print(f"no project at {project}; run `book-genesis new` first")
        return EXIT_FAILURE
    try:
        setup = _setup(args, project)
        for _ in range(8):
            phase = current_phase(project)
            if phase.label == DRAFTING_LABEL:
                break
            if load_state_summary(project)["status"] == "completed":
                break
            print(f"{phase.label}: running...", flush=True)
            result = run_phase(project, setup.adapters, setup.models)
            print(f"{result.phase}: wrote {', '.join(result.written) or 'nothing'}", flush=True)
            if not result.ok:
                print("not advanced; still missing: " + ", ".join(result.pending))
                return EXIT_FAILURE
        if current_phase(project).label == DRAFTING_LABEL:
            book = run_book(
                project,
                setup.adapters,
                setup.models,
                human_checkpoint=getattr(args, "human", False),
                panel=setup.panel,
                progress=_progress,
            )
            print(f"book: {book.status}. {book.message}", flush=True)
            if book.status == "awaiting_human":
                print(f"report so far: {project / 'RUN_REPORT.md'}")
                return EXIT_AWAITING_HUMAN
            if book.status == "blocked":
                print(f"report so far: {project / 'RUN_REPORT.md'}")
                return EXIT_BLOCKED
            advanced = advance_phase(project)
            if not advanced["ok"]:
                print("drafting done but the phase could not advance: " + ", ".join(advanced["pending"]))
                return EXIT_FAILURE
        for _ in range(6):
            if load_state_summary(project)["status"] == "completed":
                break
            phase = current_phase(project)
            print(f"{phase.label}: running...", flush=True)
            result = run_phase(project, setup.adapters, setup.models)
            print(f"{result.phase}: wrote {', '.join(result.written) or 'nothing'}", flush=True)
            if not result.ok:
                print("not advanced; still missing: " + ", ".join(result.pending))
                return EXIT_FAILURE
    except AwaitingHuman as exc:
        print(f"Awaiting a human reader: {exc}")
        return EXIT_AWAITING_HUMAN
    except AwaitingManual as exc:
        print(f"Awaiting a pasted reply: {exc}")
        return EXIT_AWAITING_MANUAL
    except (AdapterError, ValueError, FileNotFoundError, KeyError) as exc:
        print(f"Stopped: {exc}")
        return EXIT_FAILURE
    print(f"done: {project}")
    print(f"manuscript: {project / 'manuscript' / 'chapters'}")
    print(f"editorial package: {project / 'artifacts' / '10-editorial-package.md'}")
    print(f"report: {project / 'RUN_REPORT.md'}")
    return EXIT_OK


def _slug(text: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "-" for character in text.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")[:48] or "book"


def _chapter_command(args: argparse.Namespace, target: Path) -> int:
    try:
        setup = _setup(args, target)
        result = run_chapter(
            target, args.chapter, setup.adapters, models=setup.models, human_checkpoint=args.human, progress=_progress
        )
    except AwaitingHuman as exc:
        print(f"Awaiting a human reader: {exc}")
        return EXIT_AWAITING_HUMAN
    except AwaitingManual as exc:
        print(f"Awaiting a pasted reply: {exc}")
        return EXIT_AWAITING_MANUAL
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
    try:
        setup = _setup(args, target)
        result = run_book(
            target,
            setup.adapters,
            setup.models,
            start=args.start,
            end=args.end,
            human_checkpoint=args.human,
            panel=setup.panel,
            progress=_progress,
        )
    except AwaitingManual as exc:
        print(f"Awaiting a pasted reply: {exc}")
        return EXIT_AWAITING_MANUAL
    except (AdapterError, ValueError, FileNotFoundError) as exc:
        print(f"Book failed: {exc}")
        return EXIT_FAILURE

    print(f"book: {result.status} (chapters written this run: {result.chapters_done or 'none'})")
    print(result.message)
    print(f"report: {target / 'RUN_REPORT.md'}")
    if result.status == "awaiting_human":
        return EXIT_AWAITING_HUMAN
    if result.status == "blocked":
        return EXIT_BLOCKED
    return EXIT_OK


def _run_phase_command(args: argparse.Namespace, target: Path) -> int:
    try:
        setup = _setup(args, target)
        result = run_phase(target, setup.adapters, setup.models)
    except AwaitingManual as exc:
        print(f"Awaiting a pasted reply: {exc}")
        return EXIT_AWAITING_MANUAL
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


def _panel_command(args: argparse.Namespace, target: Path) -> int:
    chapter_path = target / "manuscript" / "chapters" / f"chapter-{args.chapter:02d}.md"
    if not chapter_path.exists():
        print(f"Panel failed: {chapter_path} does not exist")
        return EXIT_FAILURE
    prose = clean_chapter(chapter_path.read_text(encoding="utf-8"))
    previous_tail = ""
    previous = target / "manuscript" / "chapters" / f"chapter-{args.chapter - 1:02d}.md"
    if args.chapter > 1 and previous.exists():
        previous_tail = tail_words(previous.read_text(encoding="utf-8"), TAIL_WORDS)
    genre = load_state_summary(target).get("genre", "")
    try:
        setup = _setup(args, target)
        if setup.panel is None:
            raise AdapterError("no reader panel could be assembled")
        verdict = setup.panel.judge(prose, previous_tail, genre)
    except AwaitingManual as exc:
        print(f"Awaiting a pasted reply: {exc}")
        return EXIT_AWAITING_MANUAL
    except (AdapterError, ValueError) as exc:
        print(f"Panel failed: {exc}")
        return EXIT_FAILURE

    report = target / "evaluations" / f"chapter-{args.chapter:02d}-panel.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(verdict.raw, encoding="utf-8")
    print(f"# chapter {args.chapter} read blind by {setup.panel.label}")
    print(format_verdict(verdict))
    print(f"report: {report}")
    return EXIT_OK if verdict.turn_page else EXIT_BLOCKED


def _doctor_command() -> int:
    found = available_adapters()
    print("adapters:")
    for name in KNOWN_CLIS:
        location = shutil.which(name)
        print(f"  {name}: {'found at ' + location if location else 'not found on PATH'}")
    for name, ok in found.items():
        if name not in KNOWN_CLIS:
            print(f"  {name} (adapters.yaml): {'found' if ok else 'not found on PATH'}")
    user_config = load_user_config()
    if user_config is not None:
        print(user_config.summary())
    else:
        print("user config: none (run `book-genesis setup` to choose providers and connect keys)")
    try:
        plan = plan_roles(found, user_config)
    except AdapterError as exc:
        print(f"plan: {exc}")
        return EXIT_FAILURE
    print("roles:")
    for role in ROLES:
        role_model = plan.roles[role]
        print(f"  {role}: {role_model.adapter}{' ' + role_model.model if role_model.model else ''}")
    print("panel:")
    for spec in plan.panel:
        print(f"  {spec.adapter}{' ' + spec.model if spec.model else ''} as {spec.persona}")
    if plan.warnings:
        for warning in plan.warnings:
            print(f"warning: {warning}")
    else:
        print("warnings: none (writer and judge come from different families)")
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
