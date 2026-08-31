from unittest.mock import MagicMock, patch

from pre_commit_action.run_hooks import git_auth_env, run_precommit


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


def test_command_includes_base_ref(tmp_path):
    output = tmp_path / "out.txt"
    with patch(
        "pre_commit_action.run_hooks.subprocess.run",
        return_value=_mock_result(0, ""),
    ) as mock_run:
        run_precommit("release", "HEAD", str(output))
    cmd = mock_run.call_args[0][0]
    assert "origin/release" in cmd
    assert "--show-diff-on-failure" in cmd


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
