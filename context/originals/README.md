# Original organiser files

The unconverted files, so nobody has to trust our markdown conversions. Everything came from the organiser zip `TRUSTED_SinceAI2026_FINAL.zip` (210127444 bytes, sha256 `7962a6139902c96f7e1be2545f3320c55a28a5e846f93fa9748b2e37441b98af`), handed to participants in sinceai.app on 2026-11-06.

## In this folder (small, in git)

| File | Bytes | Converted to |
|---|---|---|
| `TrustED_PETs_Transformer_Challenge_Brief_FINAL_REVIEW.docx` | 29658 | `../brief.md` |
| `Challenge_TRUSTED_PETs_Transformer_EN.pdf` | 274465 | `../brief-onepager.md` |
| `2026.11_SinceAI_TrustEDpresentation-en-US.docx` | 7226 | `../video-transcript.md` |

The filenames lost the " (1)" download suffixes; the bytes are untouched. Hashes of each file are in `../source-files.md`.

## The video: a release asset. The proving ground: never published

The GitHub release **originals-2026-11-06** on this repository holds only the organiser intro video. Download it from the Releases page or with:

```bash
gh release download originals-2026-11-06 --repo alex-1121/team-1-trusted --pattern '*.mp4'
```

| File | Bytes | sha256 | What |
|---|---|---|---|
| `2026.11_SinceAI_TrustEDpresentation.mp4` | 99543132 | `c759e8c2f63d74dd360a82a33902fa35ab7f524bbdef1013bb92f852f1cda016` | the organiser intro video (in the release) |
| `TRUSTED_PETS_PROVING_GROUND_2026 (1).zip` | 116628228 | `b4f1b78b795812ad0b616e423d96097f262328d4635f0c6b14e0dbce9291eb77` | NOT in the release on purpose: it contains truth/, holdout/ and row maps, which must never be published; get it from sinceai.app or a teammate privately; restore steps in `../../data/README.md` |

Licences: the proving ground is CC BY 4.0 (data) and MIT (code), (c) 2026 Since AI ry, see `../proving-ground/LICENSE-DATA.md`. The brief, one-pager and video are organiser materials of the TrustED challenge (Horizon Europe grant agreement No. 101168467); redistributed here for the team, not as a TrustED deliverable.
