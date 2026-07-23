from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
from runner.distribution import (  # noqa: E402
    install_suite,
    supported_targets,
    validate_suite,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="book-genesis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a Book Genesis project tree")
    init_parser.add_argument("path")
    init_parser.add_argument("--idea", default="")
    init_parser.add_argument("--language", default="")
    init_parser.add_argument("--adapter", default="codex")
    init_parser.add_argument("--model", default="gpt-5.5")
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
    demo_parser.add_argument("--adapter", default="codex")
    demo_parser.add_argument("--model", default="gpt-5.5")

    install_parser = subparsers.add_parser("install", help="Install portable skills for an agent runtime")
    install_parser.add_argument("target", choices=supported_targets())
    install_parser.add_argument("--dest", default=None, help="Override the runtime skills directory")
    install_parser.add_argument("--include-legacy", action="store_true")
    install_parser.add_argument("--force", action="store_true", help="Back up and replace conflicting skills")
    install_parser.add_argument("--dry-run", action="store_true")

    subparsers.add_parser("verify-suite", help="Validate portable skills, agent registry, and phase contracts")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify-suite":
        result = validate_suite()
        for warning in result["warnings"]:
            print(f"warning: {warning}")
        if not result["ok"]:
            print("Portable suite validation failed")
            for error in result["errors"]:
                print(error)
            return 1
        print("Portable suite validation ok")
        return 0

    if args.command == "install":
        result = install_suite(
            args.target,
            destination=args.dest,
            include_legacy=args.include_legacy,
            force=args.force,
            dry_run=args.dry_run,
        )
        for action in result["actions"]:
            print(f"{action['action']}: {action['skill']}")
        for action in result.get("legacy_actions", []):
            print(f"{action['action']}: {action['component']}/{action['name']}")
        if not result["ok"]:
            print("Installation failed")
            for error in result["errors"]:
                print(error)
            return 1
        mode = "Dry run" if result.get("dry_run") else "Installed"
        print(f"{mode} for {args.target}: {result['destination']}")
        if result.get("backup"):
            print(f"Backup: {result['backup']}")
        return 0

    target = Path(args.path)

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
        return 0

    if args.command == "status":
        summary = load_state_summary(target)
        print(f"title={summary['title']}")
        print(f"adapter={summary['adapter']}")
        print(f"model_name={summary['model_name']}")
        print(f"current_phase={summary['current_phase']}")
        print(f"status={summary['status']}")
        return 0

    if args.command == "validate":
        result = validate_project(target)
        if not result["ok"]:
            print("Validation failed")
            for item in result["missing"]:
                print(item)
            return 1
        print("Validation ok")
        return 0

    if args.command == "prepare-phase":
        packet_path = prepare_phase(target)
        print(f"Prepared phase packet at {packet_path}")
        return 0

    if args.command == "advance-phase":
        result = advance_phase(target)
        if not result["ok"]:
            print("Advance failed")
            for item in result["pending"]:
                print(item)
            return 1
        print(f"Advanced to {result['next_phase']}")
        return 0

    if args.command == "prepare-swarm":
        run_dir = prepare_swarm_run(target, slug=args.slug, mode=args.mode)
        print(f"Prepared book-swarm run at {run_dir}")
        return 0

    if args.command == "prepare-agent-packet":
        packet_path = prepare_agent_packet(target, args.agent)
        print(f"Prepared agent packet at {packet_path}")
        return 0

    if args.command == "demo":
        create_demo(target, adapter=args.adapter, model_name=args.model)
        print(f"Created completed mechanical demo at {target}")
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
