# FAQ

## What is Book Genesis?

Book Genesis is a local, open-source Python runner for turning an author’s idea into a structured manuscript process: brief, outline, chapter attempts, blind model reads, an adversarial audit, and local review/export files. The author chooses the providers and remains responsible for the creative and editorial decisions.

## Does it create bestsellers?

No. It cannot guarantee a good book, publication readiness, sales, virality, or a human-reader response. A model-reader score is an internal process signal, not external validation. The project’s purpose is to make a more inspectable creative workflow available to more people.

## What does “blind reader” mean here?

The chapter judge receives prose and the previous chapter’s tail. It does not receive the outline, foundation documents, writer notes, or a numeric scoring rubric. On chapter 1, the runner can use several model-reader personas. These are still models, not human readers.

## Do I need an API key?

Not necessarily. You can use a logged-in Claude or Codex CLI, configure a supported provider in `book-genesis setup`, run a compatible local server, declare a CLI adapter, or use `--manual` to copy prompts to and from a chat interface. Provider usage is paid or limited according to the account or service you choose.

## Where are my manuscript and keys stored?

Projects are written locally in the project directory. Provider configuration is stored outside the repository in `~/.book-genesis/config.yaml` (or the `BOOK_GENESIS_CONFIG` location). The repository does not store keys. Do not commit personal config files, private manuscripts, or provider responses.

## Can I stop and continue later?

Yes. In the guided session, `q` saves a pending checkpoint. `book-genesis resume <project>` continues from it. Phase publication uses a local journal so an interrupted complete response can be recovered on the next run.

## What happens if an audit requests a rewrite?

The run stops at Phase 4 with `status: awaiting_revision` and exit code 4. Score and Package do not continue. Read `artifacts/08-adversarial-audit.md`, revise the manuscript yourself, and resume to request a new audit. Automatic repair is not implemented.

## How is the Genesis Score calculated?

It combines model-reader panel behavior (40%), first-draft acceptance (30%), accepted chapters (20%), and immediate remembered details (10%). See [genesis-score.md](genesis-score.md). It is not a literary grade or sales prediction.

## Does it work for every language and genre?

The runner accepts a target language and has genre profiles for common categories. The command/UI strings are primarily English; project prose follows the language selected for the book. The current beta has a real Portuguese smoke run and English/Portuguese interface coverage, not comprehensive validation across languages or literary markets. See [i18n-guide.md](i18n-guide.md).

## Can I use an existing manuscript?

You can use lower-level commands such as `judge`, `panel`, and `polish` on focused material, but importing an existing novel into the full seven-stage state machine is not a documented migration workflow. Preserve your original manuscript and test on a copy.

## Is it safe to publish generated work without review?

No. Read the work, check factual and copyright-sensitive content where applicable, use human readers and editors, and follow the requirements of the publishing path you choose. Book Genesis does not make those decisions for you.
