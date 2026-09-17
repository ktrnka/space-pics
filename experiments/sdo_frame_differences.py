"""Physics-shaped Sun signal: per channel, mean absolute difference between consecutive cached frames (6-hourly, 7 days)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spacepics.pipeline import image_cache_path
from spacepics.sources import SOURCES
from spacepics.publish import survey_candidates
from spacepics.store import read_candidates

sdo = SOURCES["sdo"]
cands = {c.key: c for c in survey_candidates(sdo) + read_candidates(sdo.name)}
by_ch = {}
for c in cands.values():
    p = image_cache_path(str(c.thumbnail_url))
    if p.exists(): by_ch.setdefault(c.instrument, []).append((c.captured_at, p))
rows = []
for ch, frames in sorted(by_ch.items()):
    frames.sort()
    prev = None; scores = []
    for t, p in frames:
        a = np.asarray(Image.open(p).convert("L").resize((256, 256)), dtype=np.float32)
        if prev is not None:
            d = np.abs(a - prev); scores.append((d.mean(), (d > 40).mean(), t, p))
        prev = a
    if not scores: continue
    scores.sort(reverse=True)
    mean = np.mean([s[0] for s in scores]); sd = np.std([s[0] for s in scores])
    print(f"{ch:10s} n={len(scores):2d} mean|diff|={mean:5.1f} sd={sd:4.1f}  top: " + ", ".join(f"{t:%m-%d %Hh} {m:.1f} ({(m-mean)/sd:+.1f}sd)" for m, f, t, p in scores[:3]))
    rows.append((ch, scores))
# contact sheet: for each channel, the top-3 changed frames and their predecessor is implied; show top-3 + bottom-1
tiles = []
for ch, scores in rows:
    for m, f, t, p in scores[:3] + scores[-1:]:
        im = Image.open(p).convert("RGB").resize((160, 160)); tiles.append(im)
sheet = Image.new("RGB", (160 * 4, 160 * len(rows)), "black")
for i, im in enumerate(tiles): sheet.paste(im, (160 * (i % 4), 160 * (i // 4)))
sheet.save("experiments/out/sheet_sdo_diff.png")
print("rows (top-3 changed, then least-changed):", [r[0] for r in rows])
