# pre-commit-action

Composite action that runs [pre-commit](https://pre-commit.com/) hooks against the PR diff and posts a sticky comment with the result.

Replaces the `style.yaml` boilerplate currently duplicated across ~20 two-inc repos.

## Usage

Copy this workflow verbatim into `.github/workflows/style.yaml`:

```yaml
name: Style

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
- Runs `uvx pre-commit run --from-ref ... --to-ref ...` against the PR diff. Pre-commit is installed in an ephemeral environment; it manages each hook's isolated environment itself.
- Posts the result as a sticky PR comment identified by the `pre-commit` header marker — the comment is updated in place across pushes instead of deleted and recreated.
- Exits with pre-commit's exit code so the job reflects pass/fail.

## Migration notes

Alongside adopting this action, consumer repos should:

- **Remove `pre-commit` from `[dependency-groups].dev`** — not needed. The action runs pre-commit via `uvx`, which installs it on the fly. Pre-commit isn't actually a project dependency.
- **Bump stale hook revisions** if any use the removed `language: python_venv` alias. Latest pre-commit (4.x) rejects this — it was deprecated in favour of `language: python`. For `docformatter`, upgrade to `v1.7.8` or later.

The action deliberately drops two things that appeared in many existing `style.yaml` files:

- **GCP Artifact Registry auth** — not needed. `uvx pre-commit` pulls pre-commit from public PyPI; no private-index access required.
- **`uv sync --group dev`** — not needed. `uvx` handles the ephemeral environment.
