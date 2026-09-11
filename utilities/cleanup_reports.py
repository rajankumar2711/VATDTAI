"""Report housekeeping for the VAT/GIDEI automation framework.

Two jobs, both safe by design:
  1. Retention  - keep only the newest N run folders under reports/runs/.
  2. Legacy purge - remove pre-consolidation clutter scattered in reports/
                    (old allure-report_*/allure-results_* dirs, top-level
                     traces/videos/logs, stray screenshots, root-level report
                     html, etc.) and clear the live allure-results collection.

It NEVER touches demo folders, __init__.py placeholders, reports/assets, or the
run folders it is asked to keep. Use --dry-run to preview, then rerun with --yes.

Examples:
  python utilities/cleanup_reports.py --dry-run
  python utilities/cleanup_reports.py --keep 5 --yes
  python utilities/cleanup_reports.py --purge-legacy --downloads --keep 5 --yes
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

# Demo folders the user maintains by hand - always preserved.
DEMO_FOLDERS = {
    "Report Module Report",
    "User Management Test reports",
    "VAT Tile Report",
}
# Files/dirs inside reports/ that must survive a purge.
PRESERVE_NAMES = {"__init__.py", "assets", "runs"}


def _dir_size_mb(path: Path) -> float:
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return round(total / (1024 * 1024), 2)


def _remove(path: Path, category: str, dry_run: bool, actions: list) -> None:
    if not path.exists():
        return
    size = _dir_size_mb(path) if path.is_dir() else round(path.stat().st_size / (1024 * 1024), 2)
    actions.append((category, str(path), size))
    if dry_run:
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except OSError:
            pass


def _clear_dir_contents(path: Path, category: str, dry_run: bool, actions: list) -> None:
    """Empty a directory but keep the directory and any __init__.py."""
    if not path.exists():
        return
    for child in path.iterdir():
        if child.name == "__init__.py":
            continue
        _remove(child, category, dry_run, actions)


def retention(reports: Path, keep: int, dry_run: bool, actions: list) -> None:
    runs = reports / "runs"
    if not runs.exists():
        return
    run_dirs = sorted(
        [d for d in runs.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for old in run_dirs[keep:]:
        _remove(old, "run folders (retention)", dry_run, actions)


def purge_legacy(reports: Path, root: Path, downloads: bool, dry_run: bool, actions: list) -> None:
    # Timestamped, pre-consolidation allure dirs.
    for d in reports.iterdir():
        if d.is_dir() and (d.name.startswith("allure-report_") or d.name.startswith("allure-results_")):
            _remove(d, "legacy allure dirs", dry_run, actions)

    # Top-level legacy artifact dirs.
    for name in ("traces", "videos", "logs", "im_shots"):
        _remove(reports / name, "legacy top-level dirs", dry_run, actions)

    if downloads:
        _clear_dir_contents(reports / "downloads", "downloads (cleared)", dry_run, actions)

    # Root-level legacy report html (reports now live under runs/).
    for html in reports.glob("*.html"):
        if html.is_file():
            _remove(html, "legacy report html", dry_run, actions)

    # Stray screenshots (both locations); keep the folders + __init__.py.
    for shots in (root / "screenshots", reports / "screenshots"):
        if shots.exists():
            for pattern in ("*.png", "*.html", "*.htm"):
                for f in shots.rglob(pattern):
                    _remove(f, "stray screenshots", dry_run, actions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean up automation report artifacts.")
    parser.add_argument("--keep", type=int, default=5, help="Run folders to keep (default 5).")
    parser.add_argument("--purge-legacy", action="store_true", help="Also remove pre-consolidation clutter.")
    parser.add_argument("--downloads", action="store_true", help="Also clear reports/downloads contents.")
    parser.add_argument("--no-clear-live-allure", action="store_true", help="Keep the live reports/allure-results.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only; delete nothing.")
    parser.add_argument("--yes", action="store_true", help="Proceed without interactive confirmation.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    reports = root / "reports"
    if not reports.exists():
        print(f"No reports directory at {reports}")
        return

    dry_run = args.dry_run or not args.yes
    actions: list = []

    retention(reports, max(args.keep, 0), dry_run, actions)
    if not args.no_clear_live_allure:
        _clear_dir_contents(reports / "allure-results", "live allure-results (cleared)", dry_run, actions)
    if args.purge_legacy:
        purge_legacy(reports, root, args.downloads, dry_run, actions)

    total = round(sum(size for _, _, size in actions), 2)
    mode = "DRY RUN (nothing deleted)" if dry_run else "DELETED"
    print(f"=== Report cleanup: {mode} ===")

    summary: dict = {}
    for category, _path, size in actions:
        count, mb = summary.get(category, (0, 0.0))
        summary[category] = (count + 1, mb + size)
    for category in sorted(summary, key=lambda c: summary[c][1], reverse=True):
        count, mb = summary[category]
        print(f"  {mb:>8.2f} MB  {count:>5} item(s)  {category}")
    print(f"--- {len(actions)} item(s), {total} MB total ---")
    if dry_run:
        print("Re-run with --yes to apply.")


if __name__ == "__main__":
    main()
