from unittest.mock import call, patch

from pre_commit_action.install_node_deps import install


def test_npm_ci(tmp_path):
    with patch("pre_commit_action.install_node_deps.subprocess.run") as mock_run:
        install("npm", str(tmp_path))
    mock_run.assert_called_once_with(["npm", "ci"], check=True)


def test_pnpm_frozen_lockfile(tmp_path):
    with patch("pre_commit_action.install_node_deps.subprocess.run") as mock_run:
        install("pnpm", str(tmp_path))
    assert mock_run.call_args_list == [
        call(["corepack", "enable"], check=True),
        call(["pnpm", "install", "--frozen-lockfile"], check=True),
    ]


def test_yarn_modern_uses_immutable(tmp_path):
    (tmp_path / ".yarnrc.yml").write_text("")
    with patch("pre_commit_action.install_node_deps.subprocess.run") as mock_run:
        install("yarn", str(tmp_path))
    assert mock_run.call_args_list == [
        call(["corepack", "enable"], check=True),
        call(["yarn", "install", "--immutable"], check=True),
    ]


def test_yarn_classic_uses_frozen_lockfile(tmp_path):
    with patch("pre_commit_action.install_node_deps.subprocess.run") as mock_run:
        install("yarn", str(tmp_path))
    assert mock_run.call_args_list == [
        call(["corepack", "enable"], check=True),
        call(["yarn", "install", "--frozen-lockfile"], check=True),
    ]
