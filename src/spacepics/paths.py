"""Repo-relative locations. Data and site outputs are kept apart from code on purpose."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
FEEDS_DIR = DATA_DIR / "feeds"  # raw feed responses, committed (offline reproducibility)
CANDIDATES_DIR = DATA_DIR / "candidates"  # extracted Candidate JSONL, committed
IMAGES_DIR = DATA_DIR / "images"  # downloaded previews, gitignored cache
PICKS_FILE = DATA_DIR / "picks.jsonl"

SITE_DIR = REPO_ROOT / "site"
POSTS_DIR = SITE_DIR / "_posts"
SITE_IMG_DIR = SITE_DIR / "assets" / "img"
DEBUG_DIR = SITE_DIR / "debug"
