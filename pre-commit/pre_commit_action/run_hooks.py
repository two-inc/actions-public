import os
import subprocess
import sys

def git_auth_env(token: str) -> dict[str, str]:
    # pre-commit clones hook repos outside the checked-out repository, where
    # actions/checkout's credentials do not apply, so on a cold cache the clone
    # is unauthenticated and git blocks prompting for a username. GIT_CONFIG_*
    # is one of the few GIT_ prefixes pre-commit lets through to git, so the
    # token reaches the clone without being written to a config file on disk.
    env = dict(os.environ)
    if not token:
        return env
    n = int(env.get("GIT_CONFIG_COUNT", "0"))
    env[f"GIT_CONFIG_KEY_{n}"] = f"url.https://x-access-token:{token}@github.com/.insteadOf"
    env[f"GIT_CONFIG_VALUE_{n}"] = "https://github.com/"
    env["GIT_CONFIG_COUNT"] = str(n + 1)
    return env


def run_precommit(base_ref: str, to_ref: str, output_path: str, token: str = "") -> int:
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
            env=git_auth_env(token),
        )
        if result.stdout:
            print(result.stdout, end="")
            f.write(result.stdout)
    return result.returncode


if __name__ == "__main__":
    base_ref = sys.argv[1]
    to_ref = sys.argv[2]
    output_path = sys.argv[3]
    sys.exit(run_precommit(base_ref, to_ref, output_path, os.environ.get("GITHUB_TOKEN", "")))
