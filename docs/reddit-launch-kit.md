# Reddit Launch Kit

Use this to relaunch Book Genesis without sounding like a repost from the old account. Lead with the result, show the repo, then explain the technical lesson.

## Positioning

Primary angle:

```text
I used AI agents to push 10+ book projects in under 30 days. I open-sourced the file-backed pipeline so it can run in Claude Code, Codex, Antigravity, Kimi, or any capable coding agent.
```

Secondary angle:

```text
The code is not a prompt pack. It is a production pipeline: state files, assumptions, phase prompts, adversarial audit, scoring, and an editorial package.
```

Technical lesson:

```text
The biggest improvement came from reducing live orchestration. More agents caught more errors, but too many simultaneous constraints made the writing worse.
```

## Suggested Reddit Title

```text
I used AI agents to push 10+ book projects in under 30 days. I open-sourced the pipeline for Claude Code, Codex, Antigravity and Kimi.
```

Alternative:

```text
I open-sourced the AI book pipeline behind 10+ book projects. Biggest lesson: fewer live agents made the books better.
```

## Reddit Body

```text
I spent the last month building and stress-testing an AI-assisted book pipeline.

The first version got huge: 17 phases, 19 skills, continuity tracking, reader simulations, scoring loops, revision agents, packaging, etc.

It caught a lot of errors.

It also started making the books worse.

The writer learned it was being judged on too many dimensions at once, so it stopped writing like a writer and started writing like a compliance engine.

So I rebuilt the system as a smaller, file-backed core that can run in Claude Code, Codex, Antigravity, Kimi, or basically any capable agent that can read/write files:

- one active phase prompt at a time
- PROJECT_STATE.yaml and ASSUMPTIONS.md
- durable artifacts instead of chat-only output
- draft before judgment
- adversarial audit before final score
- 10-dimension Genesis Score
- editorial package at the end

The repo now includes:

- the portable Book Genesis core
- the legacy V4/V5 Claude Code system
- a 10-book proof gallery with covers/cover concepts
- case studies explaining what each project taught the system
- portability notes for Claude Code, Codex, Antigravity, Kimi, and generic agents

Repo:
https://github.com/felipelobomotta-blip/book-genesis-v4

The most interesting files:

- docs/book-gallery.md
- skills/book-genesis-codex/
- docs/portability.md
- docs/book-genesis-codex.md
- SHOWCASE.md

The manuscripts are private. The repo publishes the pipeline, proof layer, cover wall, case studies, scoring artifacts, outlines/synopses where safe, and the actual portable skill.

I am curious if anyone else building long-form agent workflows has seen the same tradeoff: more orchestration improves consistency, but too many live constraints hurt voice.
```

## First Comment

```text
Small clarification because "10+ books" can sound like a fake flex:

The repo does not publish the private manuscripts. It publishes the system: pipeline, cover wall, case studies, score artifacts, outlines/synopses where safe, and the portable skill folder.

The point is not "download my books." The point is "here is the workflow that produced them, and here is what broke while testing it."
```

## Short X/Twitter Thread

```text
I used AI agents to push 10+ book projects in under 30 days.

I open-sourced the pipeline.

It works as a file-backed workflow for Claude Code, Codex, Antigravity, Kimi, or any agent that can read/write project files.
```

```text
The weird lesson:
the 17-phase / 19-skill version was not the best one.

It caught more errors.

But it also made the writer optimize for the evaluator.
```

```text
So I rebuilt it as a smaller universal core:

- one active phase at a time
- file-backed state
- explicit assumptions
- draft before scoring
- adversarial audit before final score
- editorial package at the end
```

```text
Repo:
https://github.com/felipelobomotta-blip/book-genesis-v4

The proof layer:
10+ book projects, covers/cover concepts, case studies, scoring artifacts, and the portable skill.
```

## Hacker News Title

```text
Show HN: Book Genesis - an agent-agnostic AI book pipeline
```

HN body:

```text
I built this after using AI coding agents across 10+ book projects in under 30 days.

The surprising part was that the larger version of the system - 17 phases, 19 skills, mid-draft gates, revision loops - caught more errors but often hurt the writing. The writer started optimizing for the evaluator.

The current version is smaller and agent-agnostic: durable project files, one active phase prompt at a time, adversarial audit before scoring, and an editorial package after the manuscript survives critique. It can run in Claude Code, Codex, Antigravity, Kimi, or any agent that can read and write files.

Repo:
https://github.com/felipelobomotta-blip/book-genesis-v4

Useful files:
- docs/book-gallery.md
- skills/book-genesis-codex/
- docs/portability.md
- docs/book-genesis-codex.md
- SHOWCASE.md

Interested in feedback from people building long-form agent workflows.
```
