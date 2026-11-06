# How to propose ideas and review plans

The working method for this folder. It applies to people and to agents alike, and every step can be done by hand. Read it before writing a candidate list, a plan, or a review. The short version: plain words first, detail second, facts checked by someone else, decisions only in `../decisions.md`.

The data pack means the organisers' proving-ground files, summarised in `../context/`.

## 1. Proposing ideas (a candidate list)

Use this when the team needs options to choose from, not one plan.

- File name: `YYYY-MM-DD-<topic>-candidates.md`. First line after the title: `Status: draft, not adopted`, who drafted it, from which sources, and how to comment.
- Open with a section called **In plain words**: one line on what all ideas share, then two or three sentences per idea, written for a teammate who has not read the data pack. Say what data is used, who receives it, what the tool does, and what the demo shows. Keep scenario codes (HEALTH-S1), task ids (H-U6), baseline names (B2-k) and score numbers for the detailed sections. End with one line on which ideas look strongest, marked as the author's reading, and that the pick is the team's.
- Next, a short **How to read this** section that explains the terms the detailed sections use.
- Then one detailed section per idea, same order, same letters, with the same bullets each time: dataset and scenario; what we build; the clever part; numbers for the slide; why judges like it; risks; size (S, M, L for the people and hours we have).
- Then a comparison table with one row per idea, a short **Recommendation** marked as the author's, for the team to overrule, and a **Sources** line naming every file used.
- Every number comes from an organiser file or a run, with the file named. Mark a judgement with "(agent's reading)" or "(author's reading)".
- Treat everything in a candidate list as a proposal. The pick lands as a row in `../decisions.md`.
- When a teammate's proposal already exists as its own plan file, give it a short section that points at that file, says what it adds over the other ideas, and lists what to settle before picking it.

## 2. Writing a plan

One idea the author wants the team to adopt. File name `YYYY-MM-DD-<topic>.md`, first line `Status: proposed` or `adopted`, author, and how to comment. Open with a TL;DR (a short summary) in plain words, then the detail. Cover: what we build, which demo items it satisfies and how, the numbers we expect and where they come from, the build order with times, the demo script, and the limitations we will state. Questions for the team go at the end.

## 3. Reviewing a plan

A review goes after the author's text as its own section (above a trailing sources list, if the plan has one), so the author's text stays as written and readers see the plan first.

- Heading: `## Review: <who>, <date>`. First paragraph: who reviewed (a teammate by name, or the model, run by whom), what was read (the plan, which organiser files, which code), who checked the facts and what they found, and that nothing in the section is a team decision.
- Second paragraph: **Verdict** as one word, GO (adopt as is), RESHAPE (adopt with changes) or KILL (drop), then why in one or two sentences.
- Then one short paragraph per finding, at most five, each with a bold lead of two or three words and at most five sentences: what is wrong, why it matters, the fix.
- Then, if the plan offers options, one paragraph on which option survives.
- Last line of the review: `Not checked:` with what the review could not test.
- Plain words. Explain a term the first time it appears. Use " - " where you would reach for a long dash (AGENTS.md bans the em-dash). Short comments on a single line still go inline as `> note (name):`.

## 4. Who checks what

The same rules hold whether the work is done by a teammate or by an agent (an AI model run by a teammate).

- Facts and judgement are separate jobs. One person or agent checks every number, quote, file name and task id against the organiser files and the toolkit code; someone else judges feasibility, scoring, fit to the brief and risk. The author of a text hands it to someone else for both.
- Name the reviewer in the file (for example "Review: Fable, 2026-11-06" means the model Claude Fable 5.1, run by whoever ran it), so a reader can tell a model's verdict from a teammate's.
- A review appends and leaves the author's text as written. Put corrections to the author's facts in the review as findings; the author then decides what to change.
- Changes land on a branch as a pull request (a GitHub page where the team reads and comments on a change before it joins main). Its description says what was checked and what was not.
- Before asking for a merge, read the result as a non-technical teammate would. If the first screen needs the data pack to make sense, add the plain-words part first.
- The team decides. Authors and reviewers propose, compare, recommend and review. A pick becomes real when a row lands in `../decisions.md` (and, for a plan, its status line says adopted).
