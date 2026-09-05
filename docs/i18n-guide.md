# Language and Internationalization Guide

Book Genesis separates the language of the software from the language of the book.

## Current behavior

- The command-line interface, setup flow, command help, and most technical documentation are primarily English.
- The runner accepts `--language <code>` when starting a project and stores that selection in project state.
- Phase prompts direct the model to create prose and project artifacts in the book’s selected language.
- The local review page and export coverage notice use Portuguese when the project language begins with `pt` or `por`; otherwise they use English.
- UTF-8 is used for repository resources and project artifacts.

Example:

```bash
book-genesis new --idea "Uma cidade onde cartas devolvidas mudam o passado." --language pt-BR
book-genesis new --idea "A city where returned letters alter the past." --language en
```

The language code guides the run; actual prose quality depends on the configured model, prompt, genre, and author revision. A target language is not evidence of native-level literary quality.

## Evidence and limits

The current beta has a real Portuguese-language smoke run and review-page checks in English/Portuguese paths. It has not completed systematic usability or literary validation across Spanish, French, German, Arabic, Japanese, or other language markets. Right-to-left layout has not been specifically tested.

Genre profiles define operational ranges such as chapter length, dialogue share, revision budget, and whether the disruptor runs. They do not provide language-specific literary calibration or a quality floor.

## Contributing a language improvement

Useful contributions include:

- clear translations of public documentation;
- localizing UI strings while keeping commands and paths stable;
- tests for Unicode, line endings, chapter markers, and review/export rendering;
- native-reader review of prompt wording and genre expectations.

Please do not claim that a language is “fully supported” based only on a translation or a single model response. In a pull request, state who reviewed the text, which flows were tested, and what remains unverified.

## File conventions

- Keep source files UTF-8.
- Preserve ASCII path names where practical for cross-platform command-line use.
- Do not translate machine-readable keys such as `audit_status`, project-state keys, artifact markers, or command flags.
- Keep canonical command examples in English; add localized explanation around them.
