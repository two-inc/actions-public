# pre-commit-action

Composite action that runs [pre-commit](https://pre-commit.com/) hooks against the PR diff and posts a sticky comment with the result.

Replaces the `style.yaml` boilerplate currently duplicated across ~20 two-inc repos.

## Usage

```yaml
# .github/workflows/style.yaml
name: Pre-commit

permissions: write-all

on:
  pull_request:
    types: [opened, synchronize]

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
      id-token: write
    steps:
      - uses: two-inc/pre-commit-action@v1
        with:
          python-version: "3.12"
```

## Inputs

| Input                        | Default                                                                             | Description                               |
| ---------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------- |
| `python-version`             | `3.12`                                                                              | Python version to install                 |
| `uv-group`                   | `dev`                                                                               | `uv sync` dependency group                |
| `github-token`               | `${{ github.token }}`                                                               | Token used to post the sticky comment     |
| `gcp-service-account`        | `${{ vars.GCP_ARTIFACT_REGISTRY_WRITER_SA_NAME }}`                                  | GCP SA with Artifact Registry read access |
| `workload-identity-provider` | `${{ vars.WORKLOAD_IDENTITY_PROVIDER_PREFIX }}/${{ github.event.repository.name }}` | WIF provider path                         |

## Behaviour

- Checks out the PR with full history (`fetch-depth: 0`) so pre-commit can diff against `origin/${{ github.base_ref }}`.
- Installs `uv`, sets up Python, authenticates to GCP for Artifact Registry, then `uv sync --group <uv-group>`.
- Runs pre-commit on the PR diff and captures the output.
- Posts the result as a sticky PR comment identified by the `pre-commit` header marker — the comment is updated in place across pushes instead of deleted and recreated.
- Exits with pre-commit's exit code so the job reflects pass/fail.
