import os
import sys

MAX_OUTPUT_BYTES = 60 * 1024

# pre-commit returns 1 when hooks report findings, and its own error codes
# (3 for an unexpected error, 130 for an interrupt) when it never got as far as
# running them. Those need opposite advice, so the comment must tell them apart.
HOOK_FINDINGS_EXIT_CODE = "1"


def _hint(exit_code: str, base_ref: str) -> str:
    if exit_code == "0":
        return ""

    if exit_code != HOOK_FINDINGS_EXIT_CODE:
        return f"""
pre-commit exited {exit_code} instead of reporting hook results, so this is a pre-commit
failure rather than a finding about your diff, and some or all hooks never ran.

That is one of pre-commit's own error codes (3 for an unexpected error, 130 for an
interrupt), most often a hook environment it could not install because a hook repository
would not clone. The underlying error is in the details below. Re-running the job is
usually enough; if it repeats, the action needs fixing rather than your branch.
"""

    return f"""
Looks like the PR is missing pre-commit changes. Please run the following locally and commit changes to fix this issue:

```
pre-commit install  # only if you do not have it installed already
git fetch origin
pre-commit run --from-ref origin/{base_ref} --to-ref HEAD
git commit -a
git push
```
"""


def middle_truncate(text: str, max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    buf = text.encode("utf-8")
    if len(buf) <= max_bytes:
        return text
    half = (max_bytes - 80) // 2
    removed = len(buf) - 2 * half
    head = buf[:half].decode("utf-8", errors="replace")
    tail = buf[len(buf) - half :].decode("utf-8", errors="replace")
    return f"{head}\n\n... [truncated {removed} bytes from the middle] ...\n\n{tail}"


def render_comment(
    output_path: str,
    exit_code: str,
    base_ref: str,
    actor: str,
) -> str:
    try:
        with open(output_path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError as err:
        raw = f"(failed to read {output_path}: {err})"

    output = middle_truncate(raw)
    # The step itself always succeeds (exit code is captured with -e disabled),
    # so the hook status must come from the exit code, not the step outcome.
    if exit_code == "0":
        outcome = "success"
    elif exit_code == HOOK_FINDINGS_EXIT_CODE:
        outcome = "failure"
    else:
        outcome = "error"
    emoji = "🏆" if outcome == "success" else "🚫"

    hint = _hint(exit_code, base_ref)

    return f"""# 🖌 Pre-commit {outcome} {emoji}
{hint}
<details><summary>Details</summary>

```
{output}
```

Exit code: {exit_code}

</details>

Author ✍️@{actor}"""


if __name__ == "__main__":
    output_path = sys.argv[1]
    comment_path = sys.argv[2] if len(sys.argv) > 2 else "pre-commit-comment.md"
    exit_code = os.environ.get("PRE_COMMIT_EXIT_CODE", "1")
    base_ref = os.environ.get("PRE_COMMIT_BASE_REF", "main")
    actor = os.environ.get("PRE_COMMIT_ACTOR", "ghost")
    comment = render_comment(output_path, exit_code, base_ref, actor)
    with open(comment_path, "w", encoding="utf-8") as f:
        f.write(comment)
