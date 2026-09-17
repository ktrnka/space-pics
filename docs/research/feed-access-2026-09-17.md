# Feed access survey, 2026-09-17

By a research subagent with one verification request per endpoint. "Ready" means a stable URL returning a small image
or a list, no login. Latest-style URLs (same URL, changing bytes) need a cache key that includes Last-Modified or a
fetch stage that saves the bytes itself; see the note at the end.

| Source | Spacecraft / instrument | Verified URL | Result | Cadence | Verdict |
|---|---|---|---|---|---|
| SOHO realtime | SOHO LASCO C2/C3, EIT | `https://soho.nascom.nasa.gov/data/realtime/c3/512/latest.jpg` (c2, eit171, eit195, eit284, eit304 likewise) | 200 jpeg 144 KB | roughly hourly | ready (Helioviewer already covers these with date addressing) |
| NOAA SWPC SUVI | GOES SUVI 94-304 | `https://services.swpc.noaa.gov/images/animations/suvi/primary/195/latest.png` | 200 png 700 KB, CDN cache 60 s | ~4 min | ready (Helioviewer also covers) |
| GOES-19 GeoColor | GOES-19 ABI | `https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/678x678.jpg` (also `thumbnail.jpg`; `latest.jpg` is 18 MB, avoid; timestamped files `YYYYDDDHHMM_*` alongside) | 200 jpeg 457 KB | 10 min | ready |
| NASA GIBS WMS | MODIS Terra true colour and hundreds of other layers | `https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor&CRS=EPSG:4326&BBOX=-90,-180,90,180&WIDTH=600&HEIGHT=300&FORMAT=image/png&TIME=2026-09-15` | 200 png (size unverified) | daily per layer | ready; docs prefer WMTS tiles for heavy use |
| STEREO-A beacon | STEREO-A EUVI, COR | `https://stereo-ssc.nascom.nasa.gov/beacon/latest_512/ahead_euvi_195_latest.jpg` | 200 jpeg 49 KB | ~hourly | ready (Helioviewer covers with 3-day lag; beacon is fresher) |
| NOIRLab image of the week | ground-based (Gemini, Blanco, Rubin press) | `https://noirlab.edu/public/images/iotw/feed/` | 200 rss 73 KB with `<enclosure>` JPEG URLs | weekly | ready |
| Mars Express VMC | Mars Express VMC | blog RSS 404; Flickr needs an NSID lookup; PSA archive is zipped by month | | hours after downlink | needs work |
| MSSS MARCI weather | MRO MARCI | `https://www.msss.com/msss_images/latest_weather.html` | page; current report is video (mp4/mov), no still | weekly | needs work (grab a video frame) |
| Parker WISPR | PSP WISPR | `https://wispr.nrl.navy.mil/wisprdata` | JS query form, no direct image URLs | | needs work |
| JunoCam | Juno JunoCam | `https://www.missionjuno.swri.edu/junocam/processing/` | JS app; community tools scrape PNG+JSON per image. Mission still returning data through about PJ56 (2026-03) with radiation damage degrading images | per perijove (~53 days) | needs work |
| Hope EXI | EMM EXI | `https://sdc.emiratesmarsmission.ae/data/exi` | page loads but data requires account registration | quarterly | no |
| LROC featured | LRO LROC | `https://lroc.im-ldi.com/images` | Rails app, no feed | irregular | no |
| Solar Orbiter EUI direct | SOLO EUI | `https://www.sidc.be/EUI/data-analysis` | site, not an API; Data Release 6.0 covers up to 2025-01-31, matching the 20-month lag seen in Helioviewer | | no for near-real-time |

Surprises: GOES-19 has clean unversioned latest files next to timestamped ones; NOIRLab's RSS carries real enclosures;
Hope gates behind registration despite the open-data framing; MARCI's weekly report is video-first; JunoCam is still
alive in 2026 but degrading.

Design note for latest-style URLs: the image cache is keyed by URL, so a `latest.jpg` would be fetched once and never
refreshed. Options: key the cache by URL plus Last-Modified (a HEAD per candidate), or have those sources' fetch stage
save the image bytes under a dated name as the "feed". Prefer timestamped URLs where the host offers them (GOES does;
SOHO's realtime directory may, unverified).
