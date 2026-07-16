# Claude PR Review Action

A reusable GitHub Action for automated code reviews using Claude.

## Usage

Reference this action in your workflow:

```yaml
name: Claude Code Review
on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  pull_request_review:
    types: [submitted]

permissions:
  contents: write
  actions: read
  issues: write
  id-token: write
  pull-requests: write

jobs:
  code-review:
    runs-on: ${{ vars.RUNNER_STANDARD }}
    if: |
      (
        github.event_name == 'pull_request' &&
        vars.CLAUDE_REVIEW_CONFIG != '' &&
        fromJSON(vars.CLAUDE_REVIEW_CONFIG)[format('{0}:{1}', github.base_ref, github.event.action)] == true
      ) ||
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude'))
    steps:
      # Mints a short-lived Linear token via WIF and exports it as a masked
      # LINEAR_API_KEY job env. No GCP credential is ever created on the
      # runner (access-token-only auth, no ADC file, no exported GCP env),
      # so the claude-reviewer step never sees the OAuth client secret or
      # any GCP credential. See "Linear integration" below.
      - uses: two-inc/actions/linear-token@main
        with:
          client-id: ${{ vars.LINEAR_CLIENT_ID }}
          workload-identity-provider: ${{ vars.WORKLOAD_IDENTITY_PROVIDER_PREFIX_TILLIT_API }}/${{ github.event.repository.name }}
          service-account: gha-linear-token-minter@tillit-api.iam.gserviceaccount.com

      - uses: two-inc/actions-public/claude-reviewer@main
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          github_app_client_id: ${{ vars.TWO_INC_APP_CLIENT_ID }}
          github_app_private_key: ${{ secrets.TWO_INC_APP_PRIVATE_KEY }}
```

## Configuration

### Authentication

Choose one authentication method:

**Option 1: OAuth Token (Recommended)**
1. Go to your repository Settings > Secrets and variables > Actions
2. Add `CLAUDE_CODE_OAUTH_TOKEN` with your Claude Code OAuth token
3. Use in workflow: `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`

OAuth tokens provide better security and can be rotated independently from your API key.

**Option 2: API Key (Legacy)**
1. Go to your repository Settings > Secrets and variables > Actions
2. Add `ANTHROPIC_API_KEY` with your Anthropic API key
3. Use in workflow: `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}`

You only need one authentication method.

### Linear integration (optional)

If a `LINEAR_API_KEY` is available in the environment, Claude can create Linear issues for significant problems found during review. The action itself never mints or fetches the token — it only consumes whatever `LINEAR_API_KEY` env the caller provides. This is deliberate: the review job runs an LLM with Bash access on untrusted PR content, so it must never hold GCP credentials or the Linear OAuth client secret.

**Option 1: Mint a short-lived token with `linear-token` (Recommended)**

As in the template above, a `two-inc/actions/linear-token@main` step placed before the `claude-reviewer` step (in a job with `id-token: write`) authenticates to GCP via Workload Identity Federation as `gha-linear-token-minter@tillit-api.iam.gserviceaccount.com`, mints a short-lived Linear OAuth token, and sets it as a masked `LINEAR_API_KEY` job env. It never creates a GCP credential on the runner: WIF auth is access-token-only (no ADC credentials file is written, no GCP environment variables are exported), and the OAuth client secret is fetched over the Secret Manager REST API without touching disk. By the time the `claude-reviewer` step runs, only the masked short-lived token is present — never the client secret, never any GCP credential. No persisted Linear secret is needed in GitHub (`LINEAR_CLIENT_ID` is a public org variable).

**Option 2: Inject a token directly (Legacy)**

Set `LINEAR_API_KEY` as an `env` on the action step (e.g. from a repo secret). When present, it is used as-is.

If neither is provided, the review still runs — Claude just won't create Linear issues.

## Controlling When Reviews Run

Auto-reviews are controlled by the `CLAUDE_REVIEW_CONFIG` organisation/repository variable. This is a JSON object mapping `branch:event` pairs to booleans:

```json
{"master:opened": true, "master:synchronize": true, "main:opened": true, "main:synchronize": true, "staging:opened": true}
```

This means Claude will auto-review PRs when they are opened or updated (synchronize) against `master` or `main`, and when opened against `staging`. Other branches are ignored.

Set this at the org level under Settings > Secrets and variables > Actions > Variables, or per-repo.

If `CLAUDE_REVIEW_CONFIG` is empty or unset, auto-reviews are disabled entirely. Users can still trigger reviews manually by mentioning `@claude` in a PR comment.

## Action Features

- Configurable per-branch auto-review triggers via `CLAUDE_REVIEW_CONFIG`
- Uses inline commenting for specific feedback
- Non-blocking reviews (doesn't prevent merging)
- Cost control via `--max-turns` (default: 20)
- "Fix this" links in review comments for one-click fixes
- Release PR detection with standardised summary format
- Database migration review via `two-database` plugin
- Triages unresolved review threads from bot reviewers (Claude, `*[bot]`, codex, gemini, deepsource): replies and resolves when the diff addresses them, or replies explaining when verified false positive. Human-authored threads receive a reply only — they are never auto-resolved

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `anthropic_api_key` | No | | Anthropic API key |
| `claude_code_oauth_token` | No | | Claude Code OAuth token (alternative to API key) |
| `track_progress` | No | `false` | Enable visual progress tracking comments |
| `use_sticky_comment` | No | `false` | Use sticky comments for consistent feedback |
| `settings` | No | | Claude Code settings as JSON string or path to settings JSON file |
| `plugins` | No | | Newline-separated list of Claude Code plugin names to install |
| `plugin_marketplaces` | No | `https://github.com/two-inc/agent-plugins.git` | Newline-separated list of plugin marketplace Git URLs |
| `include_fix_links` | No | `true` | Include "Fix this" links in PR review comments |
| `include_comments_by_actor` | No | | Comma-separated actor usernames to include in comment context |
| `exclude_comments_by_actor` | No | | Comma-separated actor usernames to exclude from comment context |
| `github_app_client_id` | No | | GitHub App client ID for cross-repo access (e.g. private plugin marketplaces) |
| `github_app_id` | No | | DEPRECATED — use `github_app_client_id` instead. Numeric GitHub App ID, kept as a backward-compatible alias. |
| `github_app_private_key` | No | | GitHub App private key for cross-repo access |
| `prompt` | No | *(built-in review prompt)* | Custom review prompt (replaces default) |
| `extra_prompt` | No | | Additional instructions appended to base prompt |
| `claude_args` | No | `--max-turns 20 --allowedTools ...` | Additional Claude CLI arguments |

**Note:** Provide either `anthropic_api_key` or `claude_code_oauth_token`, not both.

## Outputs

| Output | Description |
|--------|-------------|
| `session_id` | Claude Code session ID for resuming conversation |
| `structured_output` | Structured JSON output from Claude |
| `execution_file` | Path to execution output file |

## Repository-Specific Configuration

Add repository-specific review instructions via `extra_prompt`:

```yaml
      - uses: two-inc/actions-public/claude-reviewer@main
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          github_app_client_id: ${{ vars.TWO_INC_APP_CLIENT_ID }}
          github_app_private_key: ${{ secrets.TWO_INC_APP_PRIVATE_KEY }}
          extra_prompt: |

              ## Repository-Specific Guidelines:

              For this Python API codebase, pay special attention to:
              - Proper error handling and logging patterns
              - Database migration safety
              - API endpoint security and input validation
              - Test coverage for new features
              - SQLAlchemy best practices
              - Alembic migration naming conventions
```
