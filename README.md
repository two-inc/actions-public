# actions-public

Public-safe shared GitHub Actions for Two. This is the public companion to the
private [`two-inc/actions`](https://github.com/two-inc/actions) monorepo: it
holds only the actions that public repositories need, because a public repo
cannot consume an action from a private repo (GitHub blocks public-to-private
action resolution even within the org).

Each action lives in exactly one home. Public-safe actions live here; everything
else lives in the private `two-inc/actions`.

## Actions

| Action                                 | Purpose                                           |
| -------------------------------------- | ------------------------------------------------- |
| [`pre-commit`](./pre-commit)           | Run pre-commit hooks and post a sticky PR comment |
| [`claude-reviewer`](./claude-reviewer) | Run Claude Code review on pull requests           |

## Usage

```yaml
- uses: two-inc/actions-public/pre-commit@main
- uses: two-inc/actions-public/claude-reviewer@main
```

See each action's own `README.md` for inputs.
