import subprocess
import sys


def run_precommit(base_ref: str, to_ref: str, output_path: str) -> int:
    cmd = ["uvx", "pre-commit", "run"]
    # Empty base_ref happens on non-PR events (e.g. push); diffing against
    # `origin/` would fail, so fall back to checking all files.
    if base_ref:
        cmd.extend(["--from-ref", f"origin/{base_ref}", "--to-ref", to_ref])
    else:
        cmd.append("--all-files")
    cmd.append("--show-diff-on-failure")

    with open(output_path, "w", encoding="utf-8") as f:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )
        if result.stdout:
            print(result.stdout, end="")
            f.write(result.stdout)
    return result.returncode


if __name__ == "__main__":
    base_ref = sys.argv[1]
    to_ref = sys.argv[2]
    output_path = sys.argv[3]
    sys.exit(run_precommit(base_ref, to_ref, output_path))
