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
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: read
      id-token: write

    steps:
      - name: Run Claude Code Review
        uses: two-inc/claude-pr-review-action@main
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Configuration

Add your `ANTHROPIC_API_KEY` to your repository secrets:
1. Go to your repository Settings > Secrets and variables > Actions
2. Add `ANTHROPIC_API_KEY` with your Anthropic API key

## Action Features

- Triggers on PR events: opened, synchronize, ready_for_review, reopened
- Uses inline commenting for specific feedback
- Non-blocking reviews (doesn't prevent merging)
- Sticky comments for consistent feedback across PR updates
- Progress tracking with visual indicators

## Inputs

- `anthropic_api_key` (required): Your Anthropic API key
- `track_progress` (optional): Enable visual progress tracking comments (default: true)
- `use_sticky_comment` (optional): Use sticky comments for consistent feedback (default: true)
- `prompt` (optional): Custom review prompt (replaces default)
- `extra_prompt` (optional): Additional instructions appended to base prompt
- `claude_args` (optional): Additional Claude CLI arguments

## Repository-Specific Configuration

Add repository-specific review instructions:

```yaml
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