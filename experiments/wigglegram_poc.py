"""Wigglegram proof of concept: alternate left/right frames of the same tile, aligned on the centre band."""
import html, re
from pathlib import Path
import numpy as np
from PIL import Image
from spacepics.pipeline import download_url, make_client
from spacepics.sources import SOURCES
from spacepics.publish import survey_candidates
from spacepics.store import read_candidates
from spacepics.paths import DEBUG_DIR

s = SOURCES["perseverance"]
cands = {c.key: c for c in survey_candidates(s) + read_candidates("perseverance")}
def stem(c):  # NLF_1979_..._07_195J -> 1979_..._07_195J
    return re.sub(r"^[A-Z][LR][A-Z0-9]_", "", c.source_id)  # NLF/NRF, ZL0/ZR0
lefts = {stem(c): c for c in cands.values() if c.instrument in ("NAVCAM_LEFT", "MCZ_LEFT")}
rights = {stem(c): c for c in cands.values() if c.instrument in ("NAVCAM_RIGHT", "MCZ_RIGHT")}
pairs = [(lefts[k], rights[k]) for k in lefts if k in rights]
pairs.sort(key=lambda p: (-p[0].meta["sol"], p[0].captured_at))
navcam = [p for p in pairs if p[0].instrument == "NAVCAM_LEFT"]
# Mastcam-Z eyes expose minutes apart with different clocks: pair the n-th left RGB frame with the n-th right RGB frame of a sequence
from collections import defaultdict
seqs = defaultdict(lambda: {"L": [], "R": []})
for c in cands.values():
    if c.instrument in ("MCZ_LEFT", "MCZ_RIGHT") and (c.meta.get("filter_name") or "").endswith("RGB"):
        seqs[(c.meta["sol"], c.meta["sequence"])][c.instrument[4]].append(c)
mcz = []
for (sol, seq), d in sorted(seqs.items(), reverse=True):
    for l, r in zip(sorted(d["L"], key=lambda c: c.captured_at), sorted(d["R"], key=lambda c: c.captured_at)):
        mcz.append((l, r))
print(len(navcam), "navcam pairs;", len(mcz), "mastcam-z colour pairs")

def best_shift(ga, gb, ys, xs, dy_range=range(-6, 7, 2), dx_range=range(-90, 91, 2)) -> tuple[int, int, float]:
    h, w = ga.shape
    ref = ga[ys, xs]; ref = ref - ref.mean()
    best, best_dx, best_dy = -1e18, 0, 0
    for dy in dy_range:
        for dx in dx_range:
            y0, y1, x0, x1 = ys.start - dy, ys.stop - dy, xs.start - dx, xs.stop - dx
            if y0 < 0 or x0 < 0 or y1 > h or x1 > w:
                continue
            pb = gb[y0:y1, x0:x1]; pb = pb - pb.mean()
            score = (ref * pb).sum() / (np.sqrt((ref * ref).sum() * (pb * pb).sum()) + 1e-6)
            if score > best:
                best, best_dx, best_dy = score, dx, dy
    return best_dx, best_dy, float(best)


def align(a: Image.Image, b: Image.Image) -> tuple[int, int, int]:
    """Align on the centre (the subject) and measure depth spread: how far apart the best horizontal shifts are for
    the top band (far) and the bottom band (near). Big spread = a lot of parallax = slow the wiggle down."""
    ga = np.asarray(a.convert("L"), dtype=np.float32); gb = np.asarray(b.convert("L"), dtype=np.float32)
    h, w = ga.shape
    xs = slice(w // 4, 3 * w // 4)
    dx, dy, _ = best_shift(ga, gb, slice(h // 3, 2 * h // 3), xs)
    dx_far, _, _ = best_shift(ga, gb, slice(h // 8, 3 * h // 8), xs, dy_range=[dy])
    dx_near, _, _ = best_shift(ga, gb, slice(5 * h // 8, 7 * h // 8), xs, dy_range=[dy])
    return dx, dy, abs(dx_far - dx_near)


def duration_ms(spread_px: int) -> int:
    """220 ms when near and far agree; about 8 ms slower per pixel of parallax spread, capped at 600 ms."""
    return int(min(600, 220 + 8 * spread_px))


# Pick navcam pairs by measured parallax spread: enough depth to read (>= 8 px at 640 wide) but not a sliding ground
# plane (<= 40 px). Ground-looking tiles have no far background and read as translation, not depth.
def measure(pair):
    l, r = pair
    with make_client() as client:
        L = Image.open(download_url(client, str(l.preview_url))).convert("RGB")
        R = Image.open(download_url(client, str(r.preview_url))).convert("RGB")
    w = 640; L = L.resize((w, int(L.height * w / L.width))); R = R.resize(L.size)
    return align(L, R)[2]

scored = []
for pair in navcam[:24]:  # newest sols first; only cached or cheap-to-fetch previews
    try:
        scored.append((measure(pair), pair))
    except Exception as ex:
        print("skip", pair[0].source_id, ex)
good = [pair for spread, pair in sorted(scored, key=lambda t: abs(t[0] - 20)) if 8 <= spread <= 40]
print("navcam spreads:", sorted(round(sp) for sp, _ in scored))
chosen = good[:2] + mcz[:1]

out_dir = DEBUG_DIR / "img" / "wiggle"; out_dir.mkdir(parents=True, exist_ok=True)
for old in out_dir.glob("*.gif"): old.unlink()
rows = []
with make_client() as client:
    for i, (l, r) in enumerate(chosen, 1):
        L = Image.open(download_url(client, str(l.preview_url))).convert("RGB")
        R = Image.open(download_url(client, str(r.preview_url))).convert("RGB")
        w = 640; L = L.resize((w, int(L.height * w / L.width))); R = R.resize(L.size)
        chk = Image.new("RGB", (L.width * 2 + 10, L.height), "black"); chk.paste(L, (0, 0)); chk.paste(R, (L.width + 10, 0))
        chk.save(Path("experiments/out") / f"pair_check_{i}.png")
        print(f"pair {i}: L={l.source_id} R={r.source_id}")
        dx, dy, spread = align(L, R)
        R2 = Image.new("RGB", L.size, "black"); R2.paste(R, (dx, dy))
        crop = (abs(dx), abs(dy), L.width - abs(dx), L.height - abs(dy))
        frames = [L.crop(crop), R2.crop(crop)]
        ms = duration_ms(spread)
        name = f"wiggle-{l.meta['sol']}-{l.meta['sequence']}-{i}.gif"
        frames[0].save(out_dir / name, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True)
        rows.append((name, l, r, (dx, dy, spread, ms)))
        print(name, f"dx={dx} dy={dy} spread={spread}px -> {ms} ms", (out_dir / name).stat().st_size // 1024, "KB")

page = ['<!doctype html><meta charset="utf-8"><title>wigglegram experiment</title><style>body{font-family:system-ui;background:#111;color:#ddd;margin:1rem;max-width:900px} img{max-width:100%;display:block;border-radius:4px} p{color:#aaa} a{color:#8cf} h2{margin:2rem 0 .25rem}</style>',
        '<h1>Wigglegram experiment</h1><p>Left and right frames of the same tile from a stereo camera pair, taken at the same instant, alternated. The two frames are shifted to line up the centre of the scene (the subject), so things nearer or farther than the subject wobble and the eye reads depth. Pairs with a lot of depth (near and far parts shifting by very different amounts) alternate more slowly. No 3D glasses, an old trick. <a href="index.html">explorer index</a></p>']
for name, l, r, (dx, dy, spread, ms) in rows:
    page.append(f'<h2>Sol {l.meta["sol"]}, sequence {l.meta["sequence"]}, {html.escape(l.instrument.replace("_LEFT", ""))}{(" " + l.meta["filter_name"]) if l.meta.get("filter_name") else ""}</h2>'
                f'<img src="img/wiggle/{name}" alt=""><p>Aligned on the centre of the frame: shift {dx}, {dy} px at 640 px wide; parallax spread between near and far {spread} px, so {ms} ms per frame. <a href="{l.image_url}">left original</a> · <a href="{r.image_url}">right original</a> · <a href="perseverance.html#{l.meta["sequence"]}">sequence in the explorer</a></p>')
(DEBUG_DIR / "experiment-wigglegram.html").write_text("\n".join(page))
print("page written")
