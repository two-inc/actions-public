# claude-code-reviewer

Composite GitHub Action wrapping `anthropics/claude-code-action@v1` for automated PR reviews at Two Inc.

@README.md

## Rules

- Keep README.md up to date when changing inputs, outputs, defaults, or usage patterns in action.yml

## Architecture

Single-file action (`action.yml`) - no build step, no JS/TS. Thin passthrough to upstream `claude-code-action` with Two-specific defaults.

### Key design decisions

- **No checkout step** - consuming workflows handle `actions/checkout@v4` themselves
- **Pins to `@v1`** - gets semver-compatible upstream patches automatically
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
2. Point a test workflow at `two-inc/claude-code-reviewer@your-branch`
3. Open a test PR and verify the review runs correctly
4. Check GitHub Actions logs for plugin installation and review output
