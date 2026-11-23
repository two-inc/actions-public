# resolve-base-images

Reads each named `ARG`'s default from a Dockerfile and returns the same image pulled through the two-artifacts Docker Hub pull-through cache (PLAT-3046).

The Dockerfile keeps its Docker Hub image as the default, so a local `docker build` is unchanged. CI passes the cached path as a build-arg, so it never pulls from Docker Hub, which rate-limits anonymous pulls with 429s. The tag or digest is written only in the Dockerfile, so a bump there can't be overridden by a stale value in the workflow.

## Dockerfile

```dockerfile
ARG base_image="python:3.12-slim"
FROM ${base_image}
```

Declare every Docker Hub image the build pulls as a global `ARG` before the first `FROM`, one per image (`golang_image`, `composer_image` and so on).

## Usage

With `docker/build-push-action`:

```yaml
- uses: actions/checkout@v6
- id: base_images
  uses: two-inc/actions-public/resolve-base-images@main
  with:
    cache: <GAR_REGISTRY var>/<GAR_PROJECT var>/docker
- uses: docker/build-push-action@v7
  with:
    build-args: |
      commit_hash=<sha>
      <steps.base_images.outputs.build-args>
```

With the docker CLI, put `steps.base_images.outputs.build-arg-flags` in the step's `env` and expand it unquoted: `docker build $BASE_IMAGE_FLAGS -t ... .`

Expressions are written without braces above, because GitHub evaluates them anywhere in a manifest. In a workflow, wrap them in the usual expression syntax.

## Inputs

| Input | Default | Description |
|---|---|---|
| `dockerfile` | `Dockerfile` | Path to the Dockerfile. |
| `args` | `base_image` | ARG names to resolve, separated by spaces or newlines. |
| `cache` | required | Pull-through cache prefix: the `GAR_REGISTRY` and `GAR_PROJECT` org variables joined with `/docker`. Actions can't read `vars`, so the caller passes it. |
| `version-file` | empty | Optional file holding the runtime version the image must match, such as `.nvmrc`. See below. |
| `version-arg` | `base_image` | The ARG whose tag is checked against `version-file`. |

## Keeping `.nvmrc` and the image in step

A Node service keeps two versions: `.nvmrc` for local Node, and the Dockerfile's image tag for the build. Docker can't read `.nvmrc`, so the Dockerfile tag is the source for the image, and `version-file: .nvmrc` makes CI fail when the two disagree.

The check passes when the tag equals the file's version (a leading `v` is ignored) or starts with it followed by `-` or `.`. So `.nvmrc` `24` matches `node:24-alpine` and `node:24.22.1-alpine`, and `24.22.1` matches `node:24.22.1-alpine` but not `node:24-alpine` or `node:24.22.2-alpine`. Bump both in the same change.

## Outputs

| Output | Description |
|---|---|
| `build-args` | One `NAME=cached-image` line per ARG, for `build-push-action`'s `build-args`. |
| `build-arg-flags` | The same as `--build-arg NAME=cached-image` flags on one line, for the docker CLI. |
| `base_image` | The resolved `base_image`, when it is one of the args. |

Official images map to `<cache>/library/<image>`. Images with an org keep it (`apache/airflow` becomes `<cache>/apache/airflow`), and a `docker.io/` prefix is dropped. Tags and digests come through unchanged. The step fails if an ARG has no default.

The `docker` cache allows anonymous reads, so no login is needed to pull through it.
