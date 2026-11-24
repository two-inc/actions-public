# app-token

Mints a token for the two-inc org GitHub App. It's the public copy of `two-inc/actions/app-token`, for public repos, which can't call actions in a private repo.

## Where the key comes from

1. **Secret Manager (preferred).** On a `push`, `workflow_dispatch` or `schedule` run, or a `workflow_run` of a pinned release workflow, in a job with `id-token: write`, the action signs in as `gha-app-key-reader` and reads the key from Secret Manager in `two-artifacts`. Only the repo and branch pairs listed in infra `terraform/gcp/two-artifacts/core/app-key.tf` can do this.
2. **Fallback.** Otherwise it uses the `app-private-key` input, while callers still pass it. That input is the `TWO_INC_APP_PRIVATE_KEY` org secret, which is being retired (ISEC-853).

The job log says which source it used.

## Usage

```yaml
permissions:
  contents: read
  id-token: write
steps:
  - id: app-token
    uses: two-inc/actions-public/app-token@main
    with:
      client-id: CLIENT_ID_VAR
      repositories: my-repo
      permission-contents: write
  - run: gh release list
    env:
      GH_TOKEN: TOKEN_OUTPUT
```

Replace `CLIENT_ID_VAR` with the `vars.TWO_INC_APP_CLIENT_ID` expression and `TOKEN_OUTPUT` with the `steps.app-token.outputs.token` expression.

## Inputs

- `client-id`: the App's client ID.
- `app-id`: deprecated numeric App ID, used only with `app-private-key`.
- `app-private-key`: fallback key, used only when Secret Manager can't be read.
- `owner`: installation owner, `two-inc` by default.
- `repositories`: comma or newline separated repos to scope the token to. Empty means every repo the App can see.
- `permission-*`: the token's permissions. Ask for the fewest you need.

## Outputs

- `token`: the minted token, empty if none could be minted.
- `app-slug`: the App's slug.
- `source`: `secret-manager`, `input` or empty.

Keep this file in step with `two-inc/actions/app-token`.
