# pre-commit-action

Composite action that runs [pre-commit](https://pre-commit.com/) hooks against the PR diff and posts a sticky comment with the result.

Replaces the `style.yaml` boilerplate currently duplicated across ~20 two-inc repos.

## Usage

Copy this workflow verbatim into `.github/workflows/style.yaml`:

```yaml
name: Pre-commit

on:
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: pre-commit-${{ github.ref_name }}
  cancel-in-progress: true

jobs:
  pre-commit:
    runs-on: ${{ vars.RUNNER_STANDARD }}
    timeout-minutes: 20
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: two-inc/pre-commit-action@main
        with:
          python-version: "3.12"
```

## Inputs

| Input            | Default               | Description                           |
| ---------------- | --------------------- | ------------------------------------- |
| `python-version` | `3.12`                | Python version to install             |
| `github-token`   | `${{ github.token }}` | Token used to post the sticky comment |

## Behaviour

- Checks out the PR with full history (`fetch-depth: 0`) so pre-commit can diff against `origin/${{ github.base_ref }}`.
- Installs `uv` with caching enabled, sets up Python.
- Runs `uvx pre-commit run --from-ref ... --to-ref ...` against the PR diff. No project `uv sync` is performed — pre-commit manages its own hook environments.
- Posts the result as a sticky PR comment identified by the `pre-commit` header marker — the comment is updated in place across pushes instead of deleted and recreated.
- Exits with pre-commit's exit code so the job reflects pass/fail.

## Migration notes

The action deliberately drops two things that appeared in many existing `style.yaml` files:

- **GCP auth / Artifact Registry login** — not needed for pre-commit. The only private hook repo used across two-inc (`two-inc/git-hooks`) is actually public.
- **`uv sync --group dev`** — not needed. `uvx pre-commit` installs pre-commit in an ephemeral environment and pre-commit itself manages each hook's environment. No coupling to the project's dev dependencies.

If a repo genuinely needs either, add the step in its own workflow before the `uses: two-inc/pre-commit-action@main` step.
