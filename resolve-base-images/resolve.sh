#!/usr/bin/env bash
# Resolve Dockerfile ARG defaults to their two-artifacts pull-through cache paths.
# Inputs (env): DOCKERFILE, ARGS (space/newline separated), CACHE (no trailing slash),
# optional VERSION_FILE (e.g. .nvmrc) and VERSION_ARG (default base_image).
# Writes build-args, build-arg-flags and one output per ARG to $GITHUB_OUTPUT.
set -euo pipefail

: "${DOCKERFILE:?DOCKERFILE is required}"
: "${CACHE:?CACHE is required}"
: "${ARGS:?ARGS is required}"
out="${GITHUB_OUTPUT:-/dev/stdout}"
VERSION_FILE="${VERSION_FILE:-}"
VERSION_ARG="${VERSION_ARG:-base_image}"

[ -f "$DOCKERFILE" ] || { echo "::error::resolve-base-images: no Dockerfile at ${DOCKERFILE}"; exit 1; }
CACHE="${CACHE%/}"

# check_version <ref>: fail unless the ref's tag is VERSION_FILE's version, or that
# version followed by - or . (".nvmrc 24" matches node:24-alpine and node:24.22.1-alpine).
check_version() {
    local ref="$1" image tag want
    [ -f "$VERSION_FILE" ] || { echo "::error::resolve-base-images: no version file at ${VERSION_FILE}"; exit 1; }
    want=$(head -1 "$VERSION_FILE" | tr -d '\r[:space:]')
    want="${want#v}"
    [ -n "$want" ] || { echo "::error::resolve-base-images: ${VERSION_FILE} is empty"; exit 1; }
    image="${ref%%@*}"
    case "${image##*/}" in
        *:*) tag="${image##*:}" ;;
        *) tag="" ;;
    esac
    case "$tag" in
        "$want" | "$want"-* | "$want".*)
            echo "resolve-base-images: ${VERSION_ARG} tag ${tag} matches ${VERSION_FILE} (${want})" ;;
        *)
            echo "::error::resolve-base-images: ${DOCKERFILE} ARG ${VERSION_ARG} has tag '${tag}', which doesn't match ${VERSION_FILE} (${want}). Bump both together."
            exit 1 ;;
    esac
}

version_checked=0
lines=""
flags=""
for arg in $ARGS; do
    # ARG (any case) name="ref", ARG name='ref' or ARG name=ref; tolerate trailing spaces and CR.
    ref=$(sed -nE "s/^[[:space:]]*[Aa][Rr][Gg][[:space:]]+${arg}=[\"']?([^\"'[:space:]]+)[\"']?[[:space:]]*$/\1/p" "$DOCKERFILE" | tr -d '\r' | head -1)
    if [ -z "$ref" ]; then
        echo "::error::resolve-base-images: ${DOCKERFILE} has no default for ARG ${arg}"
        exit 1
    fi
    ref="${ref#docker.io/}"
    if [ -n "${VERSION_FILE:-}" ] && [ "$arg" = "${VERSION_ARG:-base_image}" ]; then
        check_version "$ref"
        version_checked=1
    fi
    case "$ref" in
        */*) path="$ref" ;;
        *) path="library/$ref" ;;
    esac
    value="${CACHE}/${path}"
    echo "resolve-base-images: ${arg}=${value}"
    lines+="${arg}=${value}"$'\n'
    flags+="--build-arg ${arg}=${value} "
    echo "${arg}=${value}" >> "$out"
done

if [ -n "${VERSION_FILE:-}" ] && [ "$version_checked" -eq 0 ]; then
    echo "::error::resolve-base-images: version-arg ${VERSION_ARG:-base_image} is not one of the args (${ARGS})"
    exit 1
fi

{
    echo "build-args<<RESOLVE_BASE_IMAGES_EOF"
    printf '%s' "$lines"
    echo "RESOLVE_BASE_IMAGES_EOF"
    echo "build-arg-flags=${flags% }"
} >> "$out"
