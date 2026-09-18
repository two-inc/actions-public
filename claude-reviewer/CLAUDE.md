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
- **Selective commenting** - prompt is heavily tuned to only flag critical issues (security, bugs, data loss, unsafe migrations). Maximum 3 comments per PR unless genuine security issues
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
  fallbacks, explicit config only, and all filtering lives in consuming
  workflows, never in action.yml (keep it a pure passthrough).

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
