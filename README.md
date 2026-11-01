<h1 align="center">Yao</h1>

<p align="center">
  <strong>Local-first developer tools in Rust · Git infrastructure contributor</strong>
</p>

<!-- BEGIN:AUTO:BADGES -->
<p align="center">
  <a href="https://github.com/sandbaseai/sandbase-harness/pulls?q=is%3Apr+author%3AAllureCurtain+is%3Amerged">
    <img alt="Merged PRs in sandbase-harness" src="https://img.shields.io/badge/sandbase--harness-414%20merged%20PRs-2563eb">
  </a>
  <a href="https://github.com/gitmono-dev/mega/pulls?q=is%3Apr+author%3AAllureCurtain+is%3Amerged">
    <img alt="Merged PRs in mega" src="https://img.shields.io/badge/mega-44%20merged%20PRs-2563eb">
  </a>
  <img alt="Rust" src="https://img.shields.io/badge/Rust-b7410e?logo=rust&logoColor=white">
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white">
  <img alt="Tauri" src="https://img.shields.io/badge/Tauri-24c8db?logo=tauri&logoColor=white">
</p>
<!-- END:AUTO:BADGES -->

---

## Open source contributions

**[sandbaseai/sandbase-harness](https://github.com/sandbaseai/sandbase-harness)** · local-first, self-hosted AI agent runtime · **<!--pr:sandbaseai/sandbase-harness-->414<!--/pr--> merged PRs**

Worked across the sandbox and session layers since mid-September 2026. Main threads:

- **Sandbox work leases** — claim, renewal, and reclaim semantics for sandboxed work; recovery of expired leases, and stopping queued work when a sandbox is released
- **Session lifecycle** — carrying a session's stop into work that arrives later, and keeping a claim scoped to one session and one environment
- **Session resources** — materializing file and repository resources for a session, and resolving the canonical in-sandbox roots on the local backend
- **Credentials** — keyed credential envelopes, excluded positions, and the boundary that keeps another server's credential undecryptable
- **Webhooks** — verifying the delivered signature off the wire, and a configurable auto-disable window
- **API conformance** — pinning wire codes, beta-header resource-family contracts, and pagination rules in tests

**[gitmono-dev/mega](https://github.com/gitmono-dev/mega)** · monorepo platform for Git · **<!--pr:gitmono-dev/mega-->44<!--/pr--> merged PRs**

Worked across the backend over roughly seven months. Main threads:

- **Code blame engine** — implemented the blame API, then refactored it onto block aggregation; fixed refs resolution and path-handling bugs
- **CL merge queue** — built the queue system, later reworked its architecture and position handling
- **Reviewer assignment** — Cedar policy-based assignment, including the secure-path implementation
- **Build triggers** — storage layer, trigger service, and task ID propagation into the build runner
- **Group permissions** — storage models, group/resource service, and the update-group API

**[libra-tools/git-internal](https://github.com/libra-tools/git-internal)** · **<!--pr:libra-tools/git-internal-->3<!--/pr--> merged PRs**

Git note object parsing and generation, plus abstracting the HTTP and SSH protocol layers out of mega into a reusable crate.

## Recent activity

<!-- BEGIN:AUTO:RECENT -->
_Most recently merged pull requests across the projects I work in._

- `2026-11-01` · [AllureCurtain/oxsum](https://github.com/AllureCurtain/oxsum/pull/525) — feat: fold observed upstream health into the route pick (issue #499)
- `2026-11-01` · [AllureCurtain/oxsum](https://github.com/AllureCurtain/oxsum/pull/524) — feat: console i18n — extract dashboard strings, ship zh-CN (issue #507)
- `2026-11-01` · [AllureCurtain/rove](https://github.com/AllureCurtain/rove/pull/51) — fix(api): widen the transcript event window for delegation runs
- `2026-11-01` · [sandbaseai/sandbase-harness](https://github.com/sandbaseai/sandbase-harness/pull/992) — docs(api): sync api.md to the bounds and rules shipped since the last pass
- `2026-11-01` · [AllureCurtain/rove](https://github.com/AllureCurtain/rove/pull/50) — fix(web): match the manual-path placeholder to the platform
- `2026-11-01` · [sandbaseai/sandbase-harness](https://github.com/sandbaseai/sandbase-harness/pull/994) — feat(scripts): add a crawl/diff tool for the official CMA docs snapshot
- `2026-11-01` · [AllureCurtain/rove](https://github.com/AllureCurtain/rove/pull/49) — fix(web): offer the provider-credentials grant inside the chat pane
- `2026-11-01` · [sandbaseai/sandbase-harness](https://github.com/sandbaseai/sandbase-harness/pull/991) — feat(deployments): enforce the published 1,000-deployment organization cap
<!-- END:AUTO:RECENT -->

## Projects

| Project | What it is | Stack |
|---|---|---|
| **[rove](https://github.com/AllureCurtain/rove)** | A local-first coding agent you can inspect, interrupt, resume, and trust. One durable runtime behind Desktop, Web, CLI, and API. | Rust · Tauri · Next.js |
| **[klip](https://github.com/AllureCurtain/klip)** | Windows clipboard manager — text, images, and files with full-text search, offline OCR, and privacy controls. | Rust · Tauri |
| **[aipop](https://github.com/AllureCurtain/aipop)** | Chrome MV3 extension for selection-based AI: translate, explain, and stream page summaries. Least-privilege, injected on demand. | TypeScript |
| **[narro](https://github.com/AllureCurtain/narro)** | Tech news reader organised into category leaderboards, with read tracking, noise filtering, and AI daily briefings. | TypeScript |

## Stats

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./profile-summary-card-output/github_dark/0-profile-details.svg">
    <img alt="Profile details" src="./profile-summary-card-output/default/0-profile-details.svg">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./profile-summary-card-output/github_dark/3-stats.svg">
    <img alt="Stats" height="200" src="./profile-summary-card-output/default/3-stats.svg">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./profile-summary-card-output/github_dark/2-most-commit-language.svg">
    <img alt="Most used languages" height="200" src="./profile-summary-card-output/default/2-most-commit-language.svg">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/streak-dark.svg">
    <img alt="Contribution streak" src="./assets/streak-light.svg">
  </picture>
</p>

<p align="center">
  <sub>
    Cards generated daily by
    <a href="https://github.com/vn7n24fzkq/github-profile-summary-cards">github-profile-summary-cards</a>,
    and the counts, recent activity and streak card by
    <a href="./scripts/update_profile.py">scripts/update_profile.py</a> —
    all committed to this repository, so they render without depending on a third-party service.
  </sub>
</p>
