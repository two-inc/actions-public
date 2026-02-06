# Claude PR Review Action

A reusable GitHub Action for automated code reviews using Claude.

## Usage

Reference this action in your workflow:

```yaml
name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize, ready_for_review, reopened]

jobs:
  claude-review:
    runs-on: ${{ vars.RUNNER_STANDARD }}
    permissions:
      contents: read
      actions: read
      pull-requests: write
      issues: read
      id-token: write

    steps:
      - uses: actions/checkout@v4
      - name: Run Claude Code Review
        uses: two-inc/claude-pr-review-action@main
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
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

## Action Features

- Triggers on PR events: opened, synchronize, ready_for_review, reopened
- Uses inline commenting for specific feedback
- Non-blocking reviews (doesn't prevent merging)
- Progress tracking with visual indicators
- Cost control via `--max-turns` (default: 10)
- "Fix this" links in review comments for one-click fixes

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `anthropic_api_key` | No | | Anthropic API key |
| `claude_code_oauth_token` | No | | Claude Code OAuth token (alternative to API key) |
| `track_progress` | No | `false` | Enable visual progress tracking comments |
| `use_sticky_comment` | No | `false` | Use sticky comments for consistent feedback |
| `settings` | No | | Claude Code settings as JSON string or path to settings JSON file |
| `plugins` | No | | Newline-separated list of Claude Code plugin names to install |
| `plugin_marketplaces` | No | `two-inc/claude-plugins` | Newline-separated list of plugin marketplace Git URLs |
| `include_fix_links` | No | `true` | Include "Fix this" links in PR review comments |
| `include_comments_by_actor` | No | | Comma-separated actor usernames to include in comment context |
| `exclude_comments_by_actor` | No | | Comma-separated actor usernames to exclude from comment context |
| `github_app_id` | No | | GitHub App ID for cross-repo access (e.g. private plugin marketplaces) |
| `github_app_private_key` | No | | GitHub App private key for cross-repo access |
| `prompt` | No | *(built-in review prompt)* | Custom review prompt (replaces default) |
| `extra_prompt` | No | | Additional instructions appended to base prompt |
| `claude_args` | No | `--max-turns 10 --allowedTools ...` | Additional Claude CLI arguments |

**Note:** Provide either `anthropic_api_key` or `claude_code_oauth_token`, not both.

## Outputs

| Output | Description |
|--------|-------------|
| `session_id` | Claude Code session ID for resuming conversation |
| `structured_output` | Structured JSON output from Claude |
| `execution_file` | Path to execution output file |

## Repository-Specific Configuration

Add repository-specific review instructions:

```yaml
- uses: actions/checkout@v4
- name: Run Claude Code Review
  uses: two-inc/claude-pr-review-action@main
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
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

## Using OAuth Token

For repositories using Claude Code OAuth authentication:

```yaml
- uses: actions/checkout@v4
- name: Run Claude Code Review
  uses: two-inc/claude-pr-review-action@main
  with:
    claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
    extra_prompt: |

      ## Repository-Specific Guidelines:
      ...
```
