# Claude PR Review Action

A reusable GitHub Action configuration for automated code reviews using Claude.

## Usage

Copy the workflow file to your repository:

```bash
mkdir -p .github/workflows/
cp claude-code-review.yaml .github/workflows/
```

## Configuration

Add your `ANTHROPIC_API_KEY` to your repository secrets:
1. Go to your repository Settings > Secrets and variables > Actions
2. Add `ANTHROPIC_API_KEY` with your Anthropic API key

## Workflow Features

- Triggers on PR events: opened, synchronize, ready_for_review, reopened
- Uses inline commenting for specific feedback
- Non-blocking reviews (doesn't prevent merging)
- Sticky comments for consistent feedback across PR updates
- Progress tracking with visual indicators

## Customization

The workflow can be customized by modifying the prompt and settings in the YAML file. See the commented examples in the workflow for different use cases.