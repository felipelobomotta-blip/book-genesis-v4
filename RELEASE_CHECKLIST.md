# Release Checklist

Steps to cut a new version of Best Seller Studio. Copy this into a GitHub Issue when preparing a release, tick items as you go.

## Pre-flight (T-2 days)

- [ ] CHANGELOG entry drafted with V[X.Y] header + sections: Added / Changed / Fixed / Deprecated / Removed
- [ ] All agents in `/agents/` reflect the new behavior; diffs reviewed
- [ ] README `Quick start` still works from a clean clone on macOS + Linux + Windows
- [ ] `install.sh` and `install.ps1` execute without errors
- [ ] Example book runs end-to-end from a fresh brief (spot-check one)
- [ ] All 8.5 gate tests pass (`tests/` folder, if applicable to the change)
- [ ] Any renamed agents/skills flagged in migration notes for existing users

## Docs

- [ ] `docs/architecture.md` updated if the pipeline diagram changed
- [ ] `docs/genesis-score.md` updated if scoring rules changed
- [ ] `docs/portability.md` updated if agent-agnostic assumptions changed
- [ ] `SHOWCASE.md` updated if a new book was shipped
- [ ] `README.md` Quality Gate badge reflects the current floor

## Version bump

- [ ] Version bumped in any manifest files
- [ ] CHANGELOG entry finalized with date
- [ ] Migration notes added if users need to adjust `~/.claude/agents/*.md`

## Tag + release

- [ ] Clean working tree (`git status`)
- [ ] Merge to `master`
- [ ] `git tag -a vX.Y.Z -m "vX.Y.Z"`
- [ ] `git push origin master --tags`
- [ ] `gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes`
- [ ] Manually edit release notes to lead with the *headline* change, not the auto-generated commit list
- [ ] Attach any new assets (demo GIF, updated architecture diagram)

## Post-release

- [ ] Pin release on GitHub
- [ ] Post release announcement in [Discussions](https://github.com/felipelobomotta-blip/book-genesis-v4/discussions/categories/announcements) (if category exists)
- [ ] Update social preview banner if the version number is on it
- [ ] Twitter/X + LinkedIn post linking the release
- [ ] Show HN or Reddit r/ClaudeAI post if the release is significant (major features, not patch)
- [ ] Update any downstream examples in `examples/` folder
- [ ] Close the release-tracking issue with the checklist

## Rollback plan

If a critical bug ships:

1. `gh release edit vX.Y.Z --draft` (unpublish without deleting)
2. Post a Discussion pinning "Known Issue: rolled back to vX.Y.(Z-1)"
3. Instruct users: `git checkout vX.Y.(Z-1) && cp agents/*.md ~/.claude/agents/`
4. Hotfix + release vX.Y.(Z+1) as fast as possible
