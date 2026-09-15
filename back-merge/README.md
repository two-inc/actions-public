# back-merge

Merge a source branch into a target branch after a release, opening a pull
request with a reviewer when the two have diverged.

Mirrored from the private `two-inc/actions` monorepo because public
repositories cannot resolve an action there. The plugin repositories are the
consumers, and three of them are public.

## Usage

```yaml
name: Merge back

on:
  push:
    branches: [main]

concurrency:
  group: merge-main
  cancel-in-progress: true

jobs:
  main-to-staging:
    name: main → staging
    runs-on: ${{ vars.RUNNER_STANDARD }}
    if: github.ref_name == 'main'
    steps:
      - uses: two-inc/actions-public/back-merge@main
        with:
          client-id: ${{ vars.TWO_INC_APP_CLIENT_ID }}
          app-private-key: ${{ secrets.TWO_INC_APP_PRIVATE_KEY }}
          source-ref: main
          target-ref: staging
          reviewer: brtkwr
```

## Inputs

| Input                   | Required | Purpose                                                         |
| ----------------------- | -------- | --------------------------------------------------------------- |
| `source-ref`            | yes      | Branch to merge from                                             |
| `target-ref`            | yes      | Branch to merge into                                             |
| `reviewer`              | yes      | Reviewer on the pull request opened when the branches conflict   |
| `client-id`             | no       | GitHub App client ID; needed to push to a protected target       |
| `app-private-key`       | no       | GitHub App private key                                           |
| `app-id`                | no       | Deprecated, use `client-id`                                      |
| `personal-access-token` | no       | Deprecated, use the App inputs                                   |

The App token is what lets the job push to a protected branch and open a pull
request that triggers downstream CI; the default `GITHUB_TOKEN` does neither.

## Behaviour

The target is reset to its remote state before merging, so a stale ref on a
persistent runner cannot fail the push. A clean merge is pushed directly. A
conflict aborts the merge and opens `merge-<source>-to-<target>` as a pull
request with the reviewer assigned.

When a conflict pull request from an earlier run is still open, the job leaves
it alone rather than resetting its branch to the source: the branch name is
deterministic, so recreating it would force-push over any resolutions the
reviewer has committed. Resolving and merging that pull request lets the next
push back-merge cleanly.

This differs from the copy in the private `two-inc/actions` monorepo, which
recreates the branch unconditionally. That path has never executed in any
repository, so the behaviour being corrected here was never relied on.
