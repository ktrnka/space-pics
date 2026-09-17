"""Repo-relative locations. Data and site outputs are kept apart from code on purpose."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
FEEDS_DIR = DATA_DIR / "feeds"  # raw feed responses, committed (offline reproducibility)
CANDIDATES_DIR = DATA_DIR / "candidates"  # extracted Candidate JSONL, committed
DERIVED_DIR = DATA_DIR / "derived"  # locally generated images (composites), gitignored; the pick's copy lives in site/
SURVEY_DIR = DATA_DIR / "survey"  # exploration fetches of other dates, gitignored; explorer pages fold them in
PICKS_FILE = DATA_DIR / "picks.jsonl"

SITE_DIR = REPO_ROOT / "site"
POSTS_DIR = SITE_DIR / "_posts"
DEBUG_DIR = SITE_DIR / "debug"


def images_dir() -> Path:
    """Downloaded previews, gitignored. Override with SPACEPICS_IMAGES_DIR so worktrees share one cache."""
    return Path(os.environ.get("SPACEPICS_IMAGES_DIR", DATA_DIR / "images"))
