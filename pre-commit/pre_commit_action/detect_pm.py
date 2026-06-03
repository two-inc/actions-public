import os
import sys


def detect_pm(workspace: str) -> str:
    if os.path.isfile(os.path.join(workspace, "pnpm-lock.yaml")):
        return "pnpm"
    if os.path.isfile(os.path.join(workspace, "yarn.lock")):
        return "yarn"
    return "npm"


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"pm={detect_pm(workspace)}")
