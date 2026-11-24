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


def _git_ok(*args: str) -> bool:
    return subprocess.run(["git", *args], capture_output=True).returncode == 0


def resolve_from_ref(base_ref: str, event_name: str) -> str:
    """Pick the ref to diff from, fetching history only when it is needed.

    On pull_request, HEAD is GitHub's test merge commit, and its first parent
    is the base tip it merged onto. The merge-base of origin/<base> and HEAD is
    always that parent (even if the base has moved on since), so HEAD^1...HEAD
    selects exactly the files origin/<base>...HEAD did, from a depth-2 checkout.
    """
    if event_name == "pull_request" and _git_ok("rev-parse", "-q", "--verify", "HEAD^2"):
        return "HEAD^1"
    # Any other event (pull_request_target checks out the base tip, which is
    # not a test merge): fetch the base with the history the merge-base needs.
    fetch = ["git", "fetch", "--no-tags"]
    if subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"], capture_output=True, text=True
    ).stdout.strip() == "true":
        fetch.append("--unshallow")
    fetch += ["origin", f"+refs/heads/{base_ref}:refs/remotes/origin/{base_ref}"]
    subprocess.run(fetch, check=True)
    return f"origin/{base_ref}"


def run_precommit(from_ref: str, to_ref: str, output_path: str, token: str = "") -> int:
    cmd = ["uvx", "pre-commit", "run"]
    # Empty from_ref happens on non-PR events (e.g. push), where there is no
    # base to diff against, so fall back to checking all files.
    if from_ref:
        cmd.extend(["--from-ref", from_ref, "--to-ref", to_ref])
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
    from_ref = resolve_from_ref(base_ref, os.environ.get("GITHUB_EVENT_NAME", "")) if base_ref else ""
    sys.exit(run_precommit(from_ref, to_ref, output_path, os.environ.get("GITHUB_TOKEN", "")))
