"""Experiment: DINOv2-small embeddings of cached images; per-instrument anomaly = cosine distance to instrument centroid."""
import json, sys, time
from pathlib import Path
import numpy as np, torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spacepics.pipeline import image_cache_path
from spacepics.sources import get_sources
from spacepics.store import read_candidates
from spacepics.publish import survey_candidates

OUT = Path("experiments/out")
t0 = time.time()
proc = AutoImageProcessor.from_pretrained("facebook/dinov2-small")
model = AutoModel.from_pretrained("facebook/dinov2-small").eval()
print(f"model load {time.time()-t0:.1f}s", flush=True)

rows = []  # (candidate, path)
for s in get_sources():
    seen = {}
    for c in survey_candidates(s) + read_candidates(s.name, days=30):
        seen[c.key] = c
    for c in seen.values():
        for url in (c.thumbnail_url, c.preview_url, c.image_url):
            if url and image_cache_path(str(url)).exists():
                rows.append((c, image_cache_path(str(url)))); break
print(f"{len(rows)} candidates with a cached image", flush=True)

embs = []
t0 = time.time()
with torch.no_grad():
    for i in range(0, len(rows), 16):
        batch = [Image.open(p).convert("RGB") for _, p in rows[i:i+16]]
        out = model(**proc(images=batch, return_tensors="pt"))
        embs.append(out.pooler_output.numpy())
E = np.concatenate(embs); E /= np.linalg.norm(E, axis=1, keepdims=True)
print(f"embedded {len(E)} images in {time.time()-t0:.1f}s ({len(E)/(time.time()-t0):.1f} img/s)", flush=True)
np.save(OUT / "embeddings.npy", E)
json.dump([{"key": c.key, "source": c.source, "instrument": c.instrument, "seq": c.meta.get("sequence"), "filter": c.meta.get("filter_name"), "path": str(p), "url": str(c.image_url)} for c, p in rows], open(OUT / "embeddings.json", "w"))

# per-instrument anomaly
groups = {}
for idx, (c, _) in enumerate(rows):
    groups.setdefault((c.source, c.instrument), []).append(idx)
scores = np.zeros(len(rows))
for (src, inst), idxs in groups.items():
    if len(idxs) < 4: continue
    cen = E[idxs].mean(axis=0); cen /= np.linalg.norm(cen)
    scores[idxs] = 1 - E[idxs] @ cen
    order = sorted(idxs, key=lambda i: -scores[i])
    print(f"\n{src}/{inst}: n={len(idxs)} mean={scores[idxs].mean():.3f}")
    for i in order[:4]: print(f"  HIGH {scores[i]:.3f} {rows[i][0].meta.get('sequence') or ''} {rows[i][0].meta.get('filter_name') or ''} {Path(rows[i][1]).name}")
    for i in order[-3:]: print(f"  low  {scores[i]:.3f} {rows[i][0].meta.get('sequence') or ''} {rows[i][0].meta.get('filter_name') or ''} {Path(rows[i][1]).name}")
np.save(OUT / "scores.npy", scores)

# contact sheets: top-8 and bottom-8 per selected instrument
def sheet(idxs, name):
    tiles = [Image.open(rows[i][1]).convert("RGB").resize((200, 150)) for i in idxs]
    im = Image.new("RGB", (200 * min(8, len(tiles)), 150 * ((len(tiles) + 7) // 8)), "black")
    for k, t in enumerate(tiles): im.paste(t, (200 * (k % 8), 150 * (k // 8)))
    im.save(OUT / f"sheet_{name}.png")
for (src, inst), idxs in groups.items():
    if len(idxs) >= 16 and src in ("perseverance", "sdo"):
        order = sorted(idxs, key=lambda i: -scores[i])
        sheet(order[:8] + order[-8:], f"{src}_{inst}".replace("/", "_"))
print("sheets written")
