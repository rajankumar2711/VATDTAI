"""Screenshot evidence helpers.

All screenshots are routed into the current run's folder (reports/runs/<run>/
screenshots) via an environment variable set by conftest at session start, so
evidence stays consolidated with traces, videos and logs.

- failure_shot(): on-failure capture, always taken.
- debug_shot():   diagnostic capture, only taken when GIDEI_DEBUG_SHOTS is set,
                  so routine runs no longer scatter/overwrite debug images.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

_ENV_DIR = "GIDEI_RUN_SCREENSHOT_DIR"
_ENV_DEBUG = "GIDEI_DEBUG_SHOTS"


def run_screenshot_dir() -> Path:
    base = os.environ.get(_ENV_DIR)
    if base:
        path = Path(base)
    else:
        path = Path(__file__).resolve().parent.parent / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def debug_shots_enabled() -> bool:
    return os.environ.get(_ENV_DEBUG, "").strip().lower() in ("1", "true", "yes", "on")


def debug_shot(page, name: str, full_page: bool = True):
    """Diagnostic screenshot, only captured when debug shots are enabled."""
    if not debug_shots_enabled():
        return None
    try:
        target = run_screenshot_dir() / f"{name}.png"
        page.screenshot(path=str(target), full_page=full_page)
        return target
    except Exception:
        return None


def failure_shot(page, name: str, full_page: bool = True):
    """On-failure screenshot, always captured into the run screenshots folder."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = run_screenshot_dir() / f"{name}_{timestamp}.png"
        page.screenshot(path=str(target), full_page=full_page)
        return target
    except Exception:
        return None
