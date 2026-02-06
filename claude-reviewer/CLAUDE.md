# claude-code-reviewer

Composite GitHub Action wrapping `anthropics/claude-code-action@v1` for automated PR reviews at Two Inc.

@README.md

## Rules

- Keep README.md up to date when changing inputs, outputs, defaults, or usage patterns in action.yml

## Architecture

Single-file action (`action.yml`) - no build step, no JS/TS. Thin passthrough to upstream `claude-code-action` with Two-specific defaults.

### How it works

1. Consuming workflow checks out the repo and calls this action
2. Action installs `gh` CLI if missing
3. Action calls `anthropics/claude-code-action@v1` with:
   - A detailed review prompt covering release PRs, regular PRs, and migration reviews
   - `--max-turns 10` for cost control
   - `--allowedTools` restricted to GitHub MCP tools + GraphQL fallback + migration validation
   - `two-database` plugin from the private `two-inc/claude-plugins` marketplace

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

- **Marketplace**: `https://github.com/two-inc/claude-plugins.git` (private, needs org-scoped GitHub token)
- **Default plugin**: `two-database` - provides Alembic/PostgreSQL migration review via `alembic-postgres-migration-helper` skill and `validate_migration.py` AST-based validation script
- Plugin names use format `plugin-name` (simple) or `plugin-name@marketplace-name` (explicit)

## Testing changes

1. Push changes to a branch
2. Point a test workflow at `two-inc/claude-pr-review-action@your-branch`
3. Open a test PR and verify the review runs correctly
4. Check GitHub Actions logs for plugin installation and review output
