# Bestseller Studio Dispatch

This layer turns Book Genesis into a specialist team. It still runs on files. Each specialist gets an agent packet, writes durable outputs, and passes explicit gates.

## Target

The craft target is a calibrated `8.5+` manuscript/package system. This is not a promise that any book will become a bestseller or go viral. It is a production threshold:

- no final score before adversarial audit
- no average-score hiding of weak floor dimensions
- no market-ready claim without product, manuscript, package, and launch gates
- no viral claim without hypothesis, framing risk, and test plan
- no independent-quality claim without evaluator isolation grade

## Team Order

1. `market_researcher`
2. `character_architect`
3. `worldbuilder` when setting, genre, history, or concept needs rules
4. `theme_engineer`
5. `plot_architect`
6. `pacing_engineer`
7. `prose_writer`
8. `continuity_editor`
9. `swarm_director`
10. `adversarial_auditor`
11. `blind_literary_critic` (at least three fresh instances)
12. `revision_editor`
13. `blind_literary_critic` again after revision
14. `scorekeeper`
15. `package_strategist`
16. `viral_framing_strategist`
17. `launch_strategist`

Loop back from any gate failure to the smallest responsible specialist. Do not rewrite the whole book when a ticket has a local owner.

## Packet Command

```bash
python runner/cli.py prepare-agent-packet my-book market_researcher
python runner/cli.py prepare-agent-packet my-book prose_writer
python runner/cli.py prepare-agent-packet my-book swarm_director
python runner/cli.py prepare-agent-packet my-book blind_literary_critic
```

Packets are written to:

```text
my-book/work/agent-packets/<agent>.md
```

## Scoring Discipline

`8.5+` means calibrated evidence after revision. Internal enthusiasm is discounted. Public reaction is scenario-based. Cultural or lived-experience approval requires human validation.

Use `skills/book-genesis/references/scoring/evaluator-protocol.md`. Writer, revision editor, and approving evaluator must use separate contexts when runtime supports them. Record Grade A, B, or C in final score.
