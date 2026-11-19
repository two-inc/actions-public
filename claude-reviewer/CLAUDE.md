# claude-code-reviewer

Composite GitHub Action wrapping `anthropics/claude-code-action@v1` for automated PR reviews at Two Inc.

@README.md

## Rules

- Keep README.md up to date when changing inputs, outputs, defaults, or usage patterns in action.yml

## Architecture

Single-file action (`action.yml`) - no build step, no JS/TS. Thin passthrough to upstream `claude-code-action` with Two-specific defaults.

### Key design decisions

- **Includes checkout step** - the composite action runs `actions/checkout@v4` itself so consuming workflows don't need to. Required because the upstream `claude-code-action` expects a git repo to exist (for `restoreConfigFromBase` security hardening)
- **Pins to `@v1`** - gets semver-compatible upstream patches automatically
- **Gates comment-driven runs on real repo permission** - the gate step sets
  `steps.gate.outputs.allowed` and every later step checks it. It runs ahead
  of the app-token step so no credential is minted for a comment we ignore.
  This duplicates a check upstream also makes; that is the point, we do not
  want a security control that lives only in a third-party action.
  Use `collaborators/{user}/permission`, never `author_association`: that
  reports `MEMBER` for any member of the owning org and `COLLABORATOR` for a
  read-only outside collaborator, so it is looser than it looks. On a public
  repo the endpoint returns `read` for any account, so requiring
  `admin`/`write` is what actually excludes strangers
- **`gh` setup runs before the gate** - the gate calls `gh api` and these
  runners do not all ship `gh`. That step installs no credential
- **`*[bot]` actors bypass the permission check** - the endpoint returns
  `none` for them (verified), so checking it would break every bot-triggered
  review. A bot identity cannot be assumed by an outside account, and
  `allowed_bots` is the filter for which bots count. Upstream does the same
- **Two review depths, picked per PR** - standard (Sonnet, 30 turns, at most 5 findings) or deep (Opus, 60 turns, three sequential lens passes in the main run, at most 10 findings). The `deep-review` label forces deep. Otherwise the `triage` step picks: the Claude Code CLI on Haiku, `--json-schema` for `{depth, category, reason}`, `continue-on-error`. The `decide` step turns that into model, turns and prompt. Any triage failure, including a non-`success` outcome, means standard, never deep. Only the enum `category` reaches the review prompt (mapped to fixed wording above the footer); the free-text reason is model output steered by PR content, so it goes to the job log only
- **Triage never runs a second claude-code-action** - that action's repo preparation is not safe twice in one job: it re-snapshots the PR's `.claude`/`CLAUDE.md` config after restoring it, replays a buffered inline-comment file, and loads the caller's settings and MCP servers. Triage installs the CLI itself and runs it in an empty temp dir holding only copies of `pr.json` and `diff.patch`, with `--tools "Read"` (Read is the only tool that exists, not just the only one allowed), `--strict-mcp-config` and no project settings. It installs the version claude-code-action pins (`const claudeCodeVersion` in `_actions/anthropics/claude-code-action/v1/src/entrypoints/run.ts`, found from `RUNNER_WORKSPACE` so a local `uses: ./claude-reviewer` works too) and passes the binary on through `path_to_claude_code_executable`, so the job downloads Claude Code once (about 200 MB of NAT traffic each on self-hosted runners). If the pin can't be read or the binary's version doesn't match it, the output stays empty and the action installs its own; `triage_claude_code_version` is only that fallback's version. Don't replace this with `actions/cache`: on self-hosted runners the cache download also goes through NAT. In a backtest Sonnet standard caught none of four known P1s and Opus deep caught three, which is why depth, not a better standard prompt, is the lever. Every finding must name a concrete failure scenario, and Claude reads callers beyond the diff. Each review ends with a footer telling the author how to ask for another review or a deep one. The deep prompt is a one-round CI variant of the `two-review-adversarial` skill, which itself is interactive-only and must not run from CI
- **One deep review per change, not per push** - PRs into main/master re-review on every push. The plan step finds Claude's last deep review (`Review depth: deep` or the `Deep review (Opus` footer) and its `commit_id`; triage then also reads `compare/<that>...<head>` and goes deep only if those changes are risky themselves. The compare is used only when its status is `ahead` or `identical`: after a rebase it would mix in base-branch changes, so triage falls back to the full diff
- **`auto-deep-review` label is informational** - added when triage (not the `deep-review` label) picks deep. It must never force deep: reusing `deep-review` would make every later push deep. Best-effort with `continue-on-error`
- **Managed vs custom callers** - an empty `claude_args` means a managed PR review (depth, skips, footer). Any caller that sets `claude_args` (backtests, sweeps) gets the plain passthrough, so those jobs keep their own model and turn budget
- **Trivial-PR skips live in the action** - Dependabot PRs and Markdown/docs-only PRs are skipped on automatic runs. This is the one exception to "filtering lives in consuming workflows": it depends on the PR's author and files, which the callers' `if:` can't see without an API call, and putting it here avoids editing ~30 workflows
- **Comment-triggered runs check out the PR head** - upstream's agent mode (always used, because we pass a prompt) never switches branch, so without this an `@claude` run reads the default branch. Same-repo PRs only: these runs hold secrets
- **Release PR detection** - auto-detects release PRs and creates summaries instead of reviews
- **Duplicate avoidance** - reads all existing comments before posting, never duplicates

## Upstream (anthropics/claude-code-action)

- Repo: https://github.com/anthropics/claude-code-action
- The upstream exposes many inputs we don't use (branching, commit signing, bedrock/vertex/foundry, trigger phrases). We only pass through what's relevant for review-only mode
- Plugin system: `plugin_marketplaces` registers Git repos as sources, `plugins` names specific plugins to install. Marketplace must be added before plugins can be installed from it

## Plugins

- **Marketplace**: `https://github.com/two-inc/agent-plugins.git` (private, needs org-scoped GitHub token)
- **Default plugin**: `two-database` - provides Alembic/PostgreSQL migration review via `alembic-postgres-migration-helper` skill and `validate_migration.py` AST-based validation script
- Plugin names use format `plugin-name` (simple) or `plugin-name@marketplace-name` (explicit)

## CLAUDE_REVIEW_CONFIG

Current org-level config: `{"master:opened":true,"master:synchronize":true,"main:opened":true,"main:synchronize":true,"staging:opened":true}`

The `if:` expression in consuming workflows evaluates this without a separate job:

```yaml
fromJSON(vars.CLAUDE_REVIEW_CONFIG)[format('{0}:{1}', github.base_ref, github.event.action)] == true
```

## Gotchas

- **Marketplace URLs must be full HTTPS** — the `org/repo` shorthand does NOT
  work in `plugin_marketplaces`; use `https://github.com/two-inc/agent-skills.git`.
- **Private marketplace auth**: the clone needs a GitHub App token
  (`actions/create-github-app-token@v1` with `TWO_INC_APP_ID` /
  `TWO_INC_APP_PRIVATE_KEY`) applied via a git URL rewrite:
  `git config --global url."https://x-access-token:TOKEN@github.com/".insteadOf "https://github.com/"`.
- **`use_sticky_comment` stays false** — sticky comments conflict with the
  "do nothing if already approved" prompt logic.
- **Session-limit failures**: when the shared `CLAUDE_CODE_OAUTH_TOKEN` hits
  its usage limit, runs fail with
  `Claude result reported subtype success with is_error:true` after ~30s —
  nothing wrong with the PR. The limit resets on the hour; rerun just the
  failed job after the reset (`gh run rerun <run-id> --failed`). During an
  exhaustion window this fails org-wide, so expect the same signature across
  repos.
- **CLAUDE_REVIEW_CONFIG stays flat** — flat `branch:event` JSON keys enable
  pure expression evaluation in consuming workflows; no wildcards or
  fallbacks, explicit config only. Branch and event filtering lives in
  consuming workflows, never in action.yml; the only filtering in the action
  is the trivial-PR skip above.
- **No subagents in a review run** - Claude Code starts Agent-tool subagents
  in the background, and claude-code-action ends the job when the main turn
  ends. A deep run that fanned out to subagents ended with "reviewers are
  still running" and posted nothing, while the job stayed green. Keep
  `Agent,Task` in `--disallowedTools`.
- **Adding the label does not start a review** - callers don't trigger on
  `labeled`. Add `deep-review`, then comment `@claude` (or push, on PRs into
  main/master).

## Adding this action to a new repo

See README.md for the full workflow YAML template. Additional conventions:

- Job name: `code-review` (not `claude-review`)
- Permissions at workflow level (not job level)
- 2-space indent unless the repo already uses 4-space for workflows
- Always include `LINEAR_API_KEY`, `github_app_id`, `github_app_private_key`
- Commit to main/master branch so it merges down to staging automatically

## Rolling out to all repos

When making changes that need to be applied across all consuming repos:

1. Commit to main/master branch (not staging) so changes merge down automatically
2. Always include Linear ticket reference in commit messages (e.g. `INF-661/feat: ...`)
3. Preserve each repo's existing indentation (2-space or 4-space) - do NOT change it
4. Try master first, then main, then staging as fallback
5. After updating master, check for merge-master-to-staging PRs that may conflict - fix by pushing master's version to staging

Repos using this action (as of Feb 2026):
claude-code-reviewer (self, uses ./), helm, admin-portal, gke-helm-deploy-action, risk-engine, communication-service, portals, checkout-page, infra (.yml), repay, e2e-tests (staging only), checkout-api, aries (staging only), njord-bank, argocd, magento-hyva-extension, openapi-action, terraform-action, magento-plugin, release-action, webhooks, platform-tools, bifrost

To find all repos: `gh search code "claude-code-reviewer" --owner two-inc --json repository,path`

## Testing changes

1. Push changes to a branch
2. Point a test workflow at `two-inc/actions/claude-reviewer@your-branch`
3. Open a test PR and verify the review runs correctly
4. Check GitHub Actions logs for plugin installation and review output
