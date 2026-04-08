from __future__ import annotations

import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_cyborg_on_path() -> Path:
    package_root = repo_root() / "Debugged_CybORG" / "CybORG"
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    return package_root
