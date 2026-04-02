#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> None:
    remove_path(ROOT / "build")
    remove_path(ROOT / "dist")
    for egg_info in ROOT.glob("*.egg-info"):
        remove_path(egg_info)


if __name__ == "__main__":
    main()
