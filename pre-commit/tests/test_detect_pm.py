from pre_commit_action.detect_pm import detect_pm


def test_detects_pnpm(tmp_path):
    (tmp_path / "pnpm-lock.yaml").write_text("")
    assert detect_pm(str(tmp_path)) == "pnpm"


def test_detects_yarn(tmp_path):
    (tmp_path / "yarn.lock").write_text("")
    assert detect_pm(str(tmp_path)) == "yarn"


def test_defaults_to_npm(tmp_path):
    assert detect_pm(str(tmp_path)) == "npm"


def test_pnpm_takes_priority_over_yarn(tmp_path):
    (tmp_path / "pnpm-lock.yaml").write_text("")
    (tmp_path / "yarn.lock").write_text("")
    assert detect_pm(str(tmp_path)) == "pnpm"
