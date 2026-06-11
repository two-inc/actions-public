from unittest.mock import MagicMock, patch

from pre_commit_action.run_hooks import run_precommit


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
