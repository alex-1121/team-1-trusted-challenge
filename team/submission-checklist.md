# Submission checklist - sinceai.app, Sunday 8 November 10:00 Turku time

Hard deadline. The platform, not Devpost. Source: the organiser builder guide on sinceai.ai and `../context/brief.md` section 07. Guide: https://sinceai.ai/hackathon-2026/guide

Status filled 2026-11-07 by the deliverables ticket (issue #19). Each line: done or missing, then what exists or who must act.

## Required fields

- [ ] Project name (80 characters) - missing. Who: team. Working title in the repo: "TrustED PETs Transformer" (`../README.md`).
- [ ] One-sentence tagline (140 characters). It is the first thing voters see on the vote card - missing. Who: team.
- [ ] Description (5,000 characters): data types identified, PET choices, protected output, measured before/after utility, one realistic sharing scenario, honest limitations - missing as form text. Who: team. Raw material: `../README.md` ("The demo in five items") and `../docs/guarantee-and-residual-risk.md`.
- [x] Built with (tech chips, five show on the vote card) - done as a pick: Python, pandas, HMAC-SHA256, k-anonymity, pets-eval (`../docs/deck-outline.md`). Who: team enters them in the form.
- [ ] Repository link (public, no data files, no secrets, no `rowmap_*.csv`, `truth/` or `holdout/`) - missing. Who: team makes the repo public after the last merge. `.gitignore` blocks data, row maps, `truth/`, `holdout/`, `out/` and the key.
- [ ] Demo video: public or unlisted YouTube link, ideally under two minutes, English narration recommended. YouTube is the only accepted format - missing. Script done (`../docs/video-script.md`, 260 spoken words). Who: team records, uploads and pastes the link.
- [ ] Source code zip, up to 100 MB, without node_modules or data files - missing. Who: team, built from a fresh clone so no gitignored file slips in.

## Optional

- [ ] Demo URL - none planned.
- [x] Up to two supporting documents (the scorecard HTML is a natural one) - available: `../results/health-s1-build/scorecard.html` and `../docs/guarantee-and-residual-risk.md`. Who: team uploads them.

## Must do even though the form calls it optional

- [ ] Pitch deck. The builder vote card shows the deck. - missing as slides. Outline done (`../docs/deck-outline.md`, 10 slides). Who: team builds and uploads the slides.

## Before pressing submit

- [ ] A fresh clone of the repo runs the demo from the README - missing, not tested by this ticket. Who: team, on a clean clone with the proving ground restored.
- [ ] The video shows all five required demo items - script covers all five (`../docs/video-script.md`); the recording is still missing. Who: team checks the recording.
- [x] Attribution line present: "TrustED PETs Proving Ground 2026, synthetic data by Since AI ry (CC BY 4.0)" - done in `../README.md`, `../docs/guarantee-and-residual-risk.md`, `../docs/video-script.md` and `../docs/deck-outline.md`. Who: team adds it to the description and the last slide.
- [ ] No real personal data, no secrets, no em-dash in anything we wrote (verbatim organiser files are exempt, see AGENTS.md) - done for the files of issue #19 (grep clean). Who: team re-checks the description and the slides.
- [ ] Every number in the description matches a scorecard run that is committed as JSON - missing until the description exists. Every number in `../README.md` and `../docs/` names its source file. Who: team.

## Also open, outside the form

- [ ] Ask on the TrustED Discord channel how to hand over `pets_submission/` without publishing row maps - open. Who: team. Details and two proposed routes: `../docs/pets-submission-handover.md`.
