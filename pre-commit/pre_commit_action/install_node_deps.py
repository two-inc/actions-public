import os
import subprocess
import sys


def install(pm: str, workspace: str) -> None:
    if pm == "pnpm":
        subprocess.run(["corepack", "enable"], check=True)
        subprocess.run(["pnpm", "install", "--frozen-lockfile"], check=True)
    elif pm == "yarn":
        subprocess.run(["corepack", "enable"], check=True)
        if os.path.isfile(os.path.join(workspace, ".yarnrc.yml")):
            subprocess.run(["yarn", "install", "--immutable"], check=True)
        else:
            subprocess.run(["yarn", "install", "--frozen-lockfile"], check=True)
    else:
        subprocess.run(["npm", "ci"], check=True)


if __name__ == "__main__":
    pm = sys.argv[1]
    workspace = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    install(pm, workspace)
