# Spacecraft, instruments, open-data tiers, and status

Research notes gathered by Keith with a separate agent on 2026-09-17; pasted here for reference. Not verified by
this repo's code. For what is actually reachable by URL for the daily build, see `docs/SOURCES.md`.

## Open-data tiers

- **Tier 1, fully open, minimal friction**: raw or lightly processed images posted publicly within hours to days, no registration.
- **Tier 2, open but delayed or gated**: public, but behind registration, a proprietary period (commonly 6 to 12 months for PI teams), or both.
- **Tier 3, curated release only**: images released via press announcements at the agency's discretion; no browsable raw archive.

Bottom line: NASA planetary and heliophysics missions are the closest thing to an open firehose (Curiosity, Perseverance,
JunoCam, SDO). ESA is open with a 6 to 12 month lag on anything not press-released. India is public but registration plus
about a year of embargo. UAE's Hope is the most open non-US mission. Treat Chinese missions' open-data claims as unverified.

## Mars

| Spacecraft | Instruments | Status | Tier | Notes |
|---|---|---|---|---|
| MRO | HiRISE, CTX, MARCI | Active since 2006 | 1 | HiRISE public site and PDS |
| Mars Odyssey | THEMIS | Active since 2001 | 1 | PDS |
| Mars Express (ESA) | HRSC, VMC | Active since 2003 | 2 | PSA with proprietary period; VMC "webcam" images released faster via ESA blogs |
| ExoMars TGO (ESA/Roscosmos) | CaSSIS | Active since 2016 | 2 | PSA embargo model |
| Hope / Al Amal (UAE) | EXI | Active since 2021 | 1 | Full raw datasets, quarterly cadence, sdc.emiratesmarsmission.ae |
| Tianwen-1 orbiter (CNSA) | remote-sensing camera | Active since 2021 | 3 | Press releases only found |
| Curiosity | Mastcam, MAHLI, Navcam | Active, landed 2012 | 1 | JPL raw galleries update within hours |
| Perseverance | Mastcam-Z, Navcam | Active, landed 2021 | 1 | Same |
| MAVEN | IUVS | Dead, declared over 2026-06-03 after losing contact 2025-12 | 1 (archival) | |
| Opportunity, Spirit, InSight, Ingenuity | | Dead | | |
| Zhurong (CNSA) | cameras | Effectively dead, hibernation since 2022-05 | 3 | |

## Moon

| Spacecraft | Instruments | Status | Tier | Notes |
|---|---|---|---|---|
| LRO | LROC | Active since 2009 | 1 | PDS and ASU LROC site; no daily feed found |
| Chang'e-4 + Yutu-2 (CNSA) | landing camera, Pancam | Active but degraded | 3 | |
| Danuri / KPLO (Korea) | LUTI, ShadowCam | Active since 2022 | 2 (partial) | ShadowCam via PDS on NASA embargo schedule |
| Chandrayaan-2 orbiter (ISRO) | OHRC, TMC-2 | Active | 2 | ISSDC/PRADAN, free registration, about a year lag |
| Chandrayaan-3, commercial landers, Chang'e-6 | | Dead or complete | | |

## Sun

| Spacecraft | Instruments | Status | Tier | Notes |
|---|---|---|---|---|
| SDO | AIA, HMI | Active since 2010 | 1 | Near real time; feeds Helioviewer |
| SOHO (ESA/NASA) | LASCO, EIT | Active since 1995 | 1 | Fully open archive |
| Parker Solar Probe | WISPR | Active since 2018 | 2 | PDS/SPDF with proprietary period |
| Solar Orbiter (ESA) | EUI, PHI | Active since 2020 | 2 | ESA archive with embargo |
| STEREO-A | cameras | Active | 1 | STEREO-B lost 2014 |

## Jupiter, Venus, Mercury

| Spacecraft | Instruments | Status | Tier | Notes |
|---|---|---|---|---|
| Juno | JunoCam | Unconfirmed; funded mission expired 2025-09-30 | 1 | Raw images posted for public processing |
| Europa Clipper | EIS | En route, arrives 2030-04 | | |
| Akatsuki (JAXA) | UVI, IR1/IR2, LIR | Dead, terminated 2025-09-18 | 1 (archival) | No Venus orbiter operating |
| BepiColombo (ESA/JAXA) | M-CAM | Final approach; orbit insertion 2026-11-21, science from 2027-04 | 2 | Flyby images via press releases; revisit December 2026 |
| MESSENGER | MDIS | Dead 2015 | 1 (archival) | |

## Deep space

| Spacecraft | Instruments | Status | Tier | Notes |
|---|---|---|---|---|
| Hubble | WFC3, ACS | Active, one-gyro mode since 2024 | 2 | MAST; about 12 month proprietary period for GO programs; press images immediate |
| JWST | NIRCam, MIRI | Active since 2022 | 2 | Same MAST model |
| New Horizons | LORRI | Active, extended mission | 1 | |
| Voyager 1 and 2 | | Cameras off since 1990 | | |
