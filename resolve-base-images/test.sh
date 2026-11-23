#!/usr/bin/env bash
# Tests for resolve.sh: run from the repo root or anywhere.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
fail=0

check() { # name expected actual
    if [ "$2" == "$3" ]; then echo "ok   $1"; else echo "FAIL $1: expected [$2] got [$3]"; fail=1; fi
}

cat > "$tmp/Dockerfile" <<'EOF'
ARG base_image="python:3.12-slim@sha256:5e2bdb1b0d54"
ARG golang_image='golang:1.27.3-alpine'
ARG airflow_image=apache/airflow
ARG hub_image="docker.io/library/node:24-alpine"
FROM ${golang_image} AS build
FROM ${base_image}
EOF
printf 'ARG crlf_image="alpine:3.24"\r\n' >> "$tmp/Dockerfile"
printf 'arg lower_image="redis:8"\n' >> "$tmp/Dockerfile"

run() { DOCKERFILE="$tmp/Dockerfile" CACHE="reg/proj/docker/" ARGS="$1" GITHUB_OUTPUT="$tmp/out" bash "$here/resolve.sh" >/dev/null; }

: > "$tmp/out"; run "base_image golang_image airflow_image hub_image crlf_image lower_image"
get() { sed -n "s/^$1=//p" "$tmp/out" | head -1; }
check "double-quoted with digest" "reg/proj/docker/library/python:3.12-slim@sha256:5e2bdb1b0d54" "$(get base_image)"
check "single-quoted" "reg/proj/docker/library/golang:1.27.3-alpine" "$(get golang_image)"
check "unquoted org image" "reg/proj/docker/apache/airflow" "$(get airflow_image)"
check "docker.io prefix stripped" "reg/proj/docker/library/node:24-alpine" "$(get hub_image)"
check "CRLF line" "reg/proj/docker/library/alpine:3.24" "$(get crlf_image)"
check "lower-case arg keyword" "reg/proj/docker/library/redis:8" "$(get lower_image)"
check "build-arg flags" "--build-arg base_image=reg/proj/docker/library/python:3.12-slim@sha256:5e2bdb1b0d54 --build-arg golang_image=reg/proj/docker/library/golang:1.27.3-alpine --build-arg airflow_image=reg/proj/docker/apache/airflow --build-arg hub_image=reg/proj/docker/library/node:24-alpine --build-arg crlf_image=reg/proj/docker/library/alpine:3.24 --build-arg lower_image=reg/proj/docker/library/redis:8" "$(sed -n 's/^build-arg-flags=//p' "$tmp/out")"
check "build-args block" "base_image=reg/proj/docker/library/python:3.12-slim@sha256:5e2bdb1b0d54" "$(sed -n '/^build-args<</,/^RESOLVE_BASE_IMAGES_EOF$/p' "$tmp/out" | sed -n 2p)"

: > "$tmp/out"
if run "missing_image" 2>/dev/null; then check "missing ARG fails" "exit!=0" "exit 0"; else check "missing ARG fails" "x" "x"; fi

# version-file checks
printf 'ARG base_image="node:24.22.1-alpine"\nARG other="node:24-alpine@sha256:abc"\nFROM ${base_image}\n' > "$tmp/Dockerfile.node"
vrun() { # args version-file-content [version-arg]
    printf '%s\n' "$2" > "$tmp/nvmrc"
    : > "$tmp/out"
    DOCKERFILE="$tmp/Dockerfile.node" CACHE="c" ARGS="$1" VERSION_FILE="$tmp/nvmrc" VERSION_ARG="${3:-base_image}" \
        GITHUB_OUTPUT="$tmp/out" bash "$here/resolve.sh" >/dev/null 2>&1
}
expect_ok() { if vrun "$@"; then check "version ok: $*" x x; else check "version ok: $*" pass fail; fi; }
expect_fail() { if vrun "$@"; then check "version mismatch fails: $*" fail pass; else check "version mismatch fails: $*" x x; fi; }
expect_ok "base_image" "24.22.1"
expect_ok "base_image" "v24.22.1"
expect_ok "base_image" "24"
expect_ok "base_image" "24.22"
expect_ok "base_image other" "24" "other"
expect_fail "base_image" "24.22.2"
expect_fail "base_image" "22"
expect_fail "base_image" "2"
expect_fail "other" "24" "base_image"
expect_fail "base_image" ""

# VERSION_ARG unset falls back to base_image
printf '24.22.1\n' > "$tmp/nvmrc"
if DOCKERFILE="$tmp/Dockerfile.node" CACHE="c" ARGS="base_image" VERSION_FILE="$tmp/nvmrc" \
    GITHUB_OUTPUT="$tmp/out" bash "$here/resolve.sh" >/dev/null 2>&1; then
    check "VERSION_ARG unset defaults to base_image" x x
else
    check "VERSION_ARG unset defaults to base_image" pass fail
fi

[ "$fail" -eq 0 ] && echo "all passed"
exit "$fail"
