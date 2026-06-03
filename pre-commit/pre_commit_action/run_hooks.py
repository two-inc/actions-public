import subprocess
import sys


def run_precommit(base_ref: str, to_ref: str, output_path: str) -> int:
    with open(output_path, "w") as f:
        result = subprocess.run(
            [
                "uvx",
                "pre-commit",
                "run",
                "--from-ref",
                f"origin/{base_ref}",
                "--to-ref",
                to_ref,
                "--show-diff-on-failure",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(result.stdout, end="")
        f.write(result.stdout)
    return result.returncode


if __name__ == "__main__":
    base_ref = sys.argv[1]
    to_ref = sys.argv[2]
    output_path = sys.argv[3]
    sys.exit(run_precommit(base_ref, to_ref, output_path))
