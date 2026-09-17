# Reference data (hand-maintained)

`instruments/<subject>.yaml`: one card per spacecraft and instrument we show. Loaded by the publisher and matched on
the exact `spacecraft` and `instrument` values that candidates carry (see `docs/SOURCES.md` and the candidate JSONL).
Cards are what a reader sees under "About this instrument" on a post and on explorer groups.

Schema (all strings unless noted; keep prose plain, no markdown headers):

```yaml
- spacecraft: Perseverance            # exact Candidate.spacecraft, or null for ground-based / varies
  instruments: [MCZ_LEFT, MCZ_RIGHT]  # exact Candidate.instrument values this card covers (one card may cover several)
  name: Mastcam-Z                      # the human name
  spacecraft_name: Perseverance rover  # human name of the vehicle, with type
  operator: NASA/JPL                   # agency or institution
  what_it_is: >                        # 2-4 sentences, plain English, for someone who has never heard of it
    ...
  what_it_sees: >                      # what the image physically shows: wavelengths, field of view, resolution, colour or not
    ...
  why_it_matters: >                    # 1-2 sentences: the science or engineering purpose
    ...
  reading_the_image: >                 # 1-3 sentences: what a viewer should look for, common artefacts, how to read the type of frame
    ...
  formal_name: Mast Camera Zoom        # optional: long official name, shown once in the card text
  instrument_labels:                   # optional: instrument value -> colloquial detail for headings
    MCZ_LEFT: left eye
    MCZ_RIGHT: right eye
  value_labels:                        # optional: meta key -> {raw value: colloquial label}
    product: {ECM: Processed image}
  wikipedia: https://en.wikipedia.org/wiki/Mastcam-Z          # instrument article if one exists, else the spacecraft article
  spacecraft_wikipedia: https://en.wikipedia.org/wiki/Perseverance_(rover)
  links: []                            # optional list of {title, url} for an official instrument page
  meta_labels:                         # optional: human labels (and units) for keys that appear in Candidate.meta for this instrument
    sol: Sol (Mars day of the mission)
    filter_name: Filter
  picture_types: []                    # optional: kinds of frame this instrument produces, to be filled from the explorer
  confidence: verified                 # verified (checked against Wikipedia or an official page) | from-memory
```
