import os
import sys

MAX_OUTPUT_BYTES = 60 * 1024


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
    outcome = "success" if exit_code == "0" else "failure"
    emoji = "🏆" if outcome == "success" else "🚫"

    hint = (
        ""
        if outcome == "success"
        else f"""
Looks like the PR is missing pre-commit changes. Please run the following locally and commit changes to fix this issue:

```
pre-commit install  # only if you do not have it installed already
git fetch origin
pre-commit run --from-ref origin/{base_ref} --to-ref HEAD
git commit -a
git push
```
"""
    )

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
