from unittest.mock import MagicMock, patch

from pre_commit_action.run_hooks import git_auth_env, resolve_from_ref, run_precommit


def _mock_result(returncode, stdout):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    return r


def test_success_returns_zero(tmp_path):
    output = tmp_path / "out.txt"
    with patch(
        "pre_commit_action.run_hooks.subprocess.run",
        return_value=_mock_result(0, "All hooks passed.\n"),
    ):
        code = run_precommit("main", "HEAD", str(output))
    assert code == 0
    assert output.read_text() == "All hooks passed.\n"


def test_failure_returns_nonzero(tmp_path):
    output = tmp_path / "out.txt"
    with patch(
        "pre_commit_action.run_hooks.subprocess.run",
        return_value=_mock_result(1, "Hook failed.\n"),
    ):
        code = run_precommit("main", "HEAD", str(output))
    assert code == 1
    assert output.read_text() == "Hook failed.\n"


def test_command_includes_from_ref(tmp_path):
    output = tmp_path / "out.txt"
    with patch(
        "pre_commit_action.run_hooks.subprocess.run",
        return_value=_mock_result(0, ""),
    ) as mock_run:
        run_precommit("HEAD^1", "HEAD", str(output))
    cmd = mock_run.call_args[0][0]
    assert cmd[cmd.index("--from-ref") + 1] == "HEAD^1"
    assert cmd[cmd.index("--to-ref") + 1] == "HEAD"
    assert "--show-diff-on-failure" in cmd


def _git(returncode=0, stdout=""):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    return r


def test_resolve_from_ref_uses_merge_parent_on_pull_request():
    with patch("pre_commit_action.run_hooks.subprocess.run", return_value=_git(0)) as mock_run:
        assert resolve_from_ref("staging", "pull_request") == "HEAD^1"
    # Only the HEAD^2 probe ran: nothing was fetched.
    assert mock_run.call_count == 1
    assert mock_run.call_args[0][0][:2] == ["git", "rev-parse"]


def test_resolve_from_ref_fetches_base_when_head_is_not_a_merge():
    calls = []

    def fake_run(cmd, **_kwargs):
        calls.append(cmd)
        if cmd[-1] == "HEAD^2":
            return _git(1)
        if "--is-shallow-repository" in cmd:
            return _git(0, "true\n")
        return _git(0)

    with patch("pre_commit_action.run_hooks.subprocess.run", side_effect=fake_run):
        assert resolve_from_ref("main", "pull_request") == "origin/main"
    assert calls[-1] == [
        "git", "fetch", "--no-tags", "--unshallow", "origin",
        "+refs/heads/main:refs/remotes/origin/main",
    ]


def test_resolve_from_ref_ignores_merge_parent_outside_pull_request():
    # pull_request_target checks out the base tip, which can itself be a merge
    # commit; its first parent is not the PR's base.
    calls = []

    def fake_run(cmd, **_kwargs):
        calls.append(cmd)
        if "--is-shallow-repository" in cmd:
            return _git(0, "false\n")
        return _git(0)

    with patch("pre_commit_action.run_hooks.subprocess.run", side_effect=fake_run):
        assert resolve_from_ref("main", "pull_request_target") == "origin/main"
    assert ["git", "rev-parse", "-q", "--verify", "HEAD^2"] not in calls
    assert calls[-1] == [
        "git", "fetch", "--no-tags", "origin",
        "+refs/heads/main:refs/remotes/origin/main",
    ]


def test_command_empty_base_ref_uses_all_files(tmp_path):
    output = tmp_path / "out.txt"
    with patch(
        "pre_commit_action.run_hooks.subprocess.run",
        return_value=_mock_result(0, ""),
    ) as mock_run:
        run_precommit("", "HEAD", str(output))
    cmd = mock_run.call_args[0][0]
    assert "--all-files" in cmd
    assert "--from-ref" not in cmd
    assert "--show-diff-on-failure" in cmd


def test_git_auth_env_rewrites_github_url():
    with patch.dict("os.environ", {}, clear=True):
        env = git_auth_env("ghs_token")
    assert env["GIT_CONFIG_COUNT"] == "1"
    assert env["GIT_CONFIG_KEY_0"] == "url.https://x-access-token:ghs_token@github.com/.insteadOf"
    assert env["GIT_CONFIG_VALUE_0"] == "https://github.com/"


def test_git_auth_env_without_token_adds_nothing():
    with patch.dict("os.environ", {}, clear=True):
        env = git_auth_env("")
    assert "GIT_CONFIG_COUNT" not in env
    assert not [k for k in env if k.startswith("GIT_CONFIG_KEY_")]


def test_git_auth_env_appends_to_existing_config():
    existing = {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.pager",
        "GIT_CONFIG_VALUE_0": "cat",
    }
    with patch.dict("os.environ", existing, clear=True):
        env = git_auth_env("ghs_token")
    assert env["GIT_CONFIG_COUNT"] == "2"
    assert env["GIT_CONFIG_KEY_0"] == "core.pager"
    assert env["GIT_CONFIG_KEY_1"] == "url.https://x-access-token:ghs_token@github.com/.insteadOf"


def test_token_reaches_the_subprocess(tmp_path):
    output = tmp_path / "out.txt"
    with patch.dict("os.environ", {}, clear=True):
        with patch(
            "pre_commit_action.run_hooks.subprocess.run",
            return_value=_mock_result(0, ""),
        ) as mock_run:
            run_precommit("main", "HEAD", str(output), "ghs_token")
    env = mock_run.call_args.kwargs["env"]
    assert env["GIT_CONFIG_VALUE_0"] == "https://github.com/"
