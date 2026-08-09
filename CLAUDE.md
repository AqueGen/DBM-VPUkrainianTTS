# DBM-VPUkrainianTTS

Ukrainian female TTS voice pack for Deadly Boss Mods, generated with ElevenLabs.

## Release Process

Releases are driven by [release-please](https://github.com/googleapis/release-please) from **Conventional Commits**. Nothing is versioned by hand.

- Write commits as `feat: ...` (minor), `fix: ...` (patch), `feat!: ...` or a `BREAKING CHANGE:` footer (major). Anything else (`chore:`, `docs:`, `ci:`, `refactor:`) does not trigger a release on its own.
- On every push to `main`, `release-please.yml` opens or updates a **release PR** that bumps `## Version:` in `DBM-VPUkrainianTTS_Mainline.toc`, updates `CHANGELOG.md`, and updates `.release-please-manifest.json`.
- **Merging that PR** publishes everything: the `v<semver>` tag, the GitHub release, and - in the same workflow run - the CurseForge/Wago upload.
- The packaging job lives in `release-please.yml` on purpose. A tag pushed with the default `GITHUB_TOKEN` does **not** trigger other workflows, so `release.yml` would never fire for a release-please tag. `release.yml` is now `workflow_dispatch` only and exists for manual builds.
- `CHANGELOG.md` is **generated and accumulating** — release-please owns it. Do NOT hand-edit it and do NOT overwrite it with a single release's notes. The packager gets only the newest section, via `RELEASE_NOTES.md`, which CI extracts from `CHANGELOG.md` before packaging (it is gitignored and excluded from the zip).
- Version headings in `CHANGELOG.md` must stay in the `## [x.y.z]` form — the extraction stops at the next `## [` heading.
- Never edit the `## Version:` line in the TOC by hand — it sits inside `# x-release-please-start-version` / `# x-release-please-end` markers. The TOC holds bare semver (`1.2.0`); tags keep the `v` prefix (`v1.2.0`).
- `## X-DBM-Voice-Version:` is the **DBM sound registry version**, not the addon version. release-please does not touch it, and it must not be bumped for a release.
- **NEVER** delete, force-push, or recreate tags/releases. CurseForge picks up every tag push and creates duplicate entries that cannot be removed. Always let a new release PR produce the next version instead.
