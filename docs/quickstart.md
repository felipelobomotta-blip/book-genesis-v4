# Quickstart

Book Genesis is a local, provider-agnostic writing runner. You bring the idea, the choices, and the creative direction. It coordinates a structured draft-and-read process around the model providers you choose.

It is a technical beta. It can help make a manuscript, preserve its history, and surface editorial problems. It cannot promise a bestseller, publication readiness, sales, or a response from human readers.

## Before you begin

- Python 3.10 or later.
- A supported route to a text model: a logged-in `claude` or `codex` CLI, a provider you configure in `setup`, a compatible local server, a declared CLI adapter, or `--manual`.
- An idea you care enough about to revise. The program is designed to keep authorship in the loop; it does not replace taste, lived experience, or editorial judgment.

Clone the repository and install the local checkout:

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4.git
cd book-genesis-v4
python -m pip install -e .
book-genesis --help
```

The project is not published as a hosted service. `pip install -e .` installs the copy you cloned. For a portable local build, create a wheel with:

```bash
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
```

## Connect a provider

Run the setup wizard once:

```bash
book-genesis setup
book-genesis doctor
```

`setup` detects compatible local CLIs, configured key variables, and local servers; it can also configure supported HTTP providers. It keeps personal configuration in `~/.book-genesis/config.yaml` (or `BOOK_GENESIS_CONFIG`). Do not commit that file. Keys are not stored in this repository, prompts, or run logs.

Book Genesis uses your own provider accounts and subscriptions. Model use can cost money. The number of calls depends on genre, chapter count, and revision cycles, so inspect `doctor` and your provider's pricing before a long run.

If you have no CLI or API route, use manual mode. The runner writes each prompt to `work/manual/`; paste a model's response into the matching response file and repeat the command. Manual mode exits with code 5 while waiting for a reply.

## Create a book

Start an interactive run:

```bash
book-genesis new --idea "A night-shift archivist discovers that returned library books remember their readers." --language en
```

You can also let the command ask for the idea, choose a project folder, or keep the session fully non-interactive:

```bash
book-genesis new
book-genesis new --idea "..." --language en --path books/returned-books --yes --plain
```

The guided session pauses after the brief, the outline, and a blind reading of chapter 1. Press Enter to continue. Type feedback to save it as author notes and rerun that checkpointed stage. Type `q` to stop safely, then continue later:

```bash
book-genesis resume books/returned-books
```

Use `--human` to require a deliberate human approval after chapter 1. The choice is saved with that project, so every later `resume` continues to require `approve` even when invoked with `--yes`. Without it, the model-reader panel runs and the session continues automatically. Use `--chapters N` for a limited run.

## Read and export

Every project remains a local directory containing its manuscript, drafts, verdicts, artifacts, state, and report. Generate a local reader page or exports when you are ready to inspect them:

```bash
book-genesis review books/returned-books
book-genesis review books/returned-books --open
book-genesis export books/returned-books --format markdown
book-genesis export books/returned-books --format epub --output releases/returned-books.epub
```

`review` creates `review/index.html`; it does not upload the manuscript. `export` writes canonical chapters only, labels incomplete work as partial, and refuses to overwrite an existing export unless you add `--overwrite`.

## If the audit stops the run

The manuscript-level audit must end with exactly one status: `audit_status: pass`, `audit_status: revise`, or `audit_status: major_rewrite`. The last two stop the session at Audit, preserve the report, and return exit code 4. Score and Package do not run.

Read `artifacts/08-adversarial-audit.md`, revise the canonical manuscript yourself, and run `book-genesis resume <project>`. The runner audits again. There is no automatic structural repair command.

## Common local commands

```bash
book-genesis doctor
python -m runner status books/returned-books
python -m runner validate books/returned-books
python -m runner chapter books/returned-books 1 --manual
python -m runner panel books/returned-books 1
python -m runner judge path/to/chapter.md --genre thriller --adapter codex
```

For the full command reference, exit codes, adapters, and operational limits, read [runner.md](runner.md).
