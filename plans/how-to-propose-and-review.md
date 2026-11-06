# How to propose ideas and review plans

The working method for this folder. It applies to people and to agents alike. Read it before writing a candidate list, a plan, or a review. The short version: plain words first, detail second, facts checked by someone else, decisions only in `../decisions.md`.

## 1. Proposing ideas (a candidate list)

Use this when the team needs options to choose from, not one plan.

- File name: `YYYY-MM-DD-<topic>-candidates.md`. First line after the title: `Status: draft, not adopted`, who drafted it, and from which sources.
- Open with a section called **In plain words**: two or three sentences per idea, written for a teammate who has not read the data pack. Say what data is used, who receives it, what the tool does, and what the demo shows. No scenario codes, task ids, baseline names or score numbers in this section. End it with one line on which ideas are live and that the pick is the team's.
- Then one detailed section per idea, same order, same letters, with the same bullets each time: dataset and scenario; what we build; the clever part; numbers for the slide; why judges like it; risks; size (S, M, L for the people and hours we have).
- Then a comparison table with one row per idea, and a short **Recommendation** marked as the author's, for the team to overrule.
- Every number comes from an organiser file or a run, with the file named. A judgement is marked as such: "(author's reading)" or "Our reading:".
- Nothing in a candidate list is a decision. The pick lands as a row in `../decisions.md`.
- A teammate's own proposal that already exists gets a section in the list that points at their file, with the same bullets, so the comparison is fair.

## 2. Writing a plan

One idea the author wants the team to adopt. File name `YYYY-MM-DD-<topic>.md`, first line `Status: proposed` or `adopted`, author, and how to comment. Open with a TL;DR in plain words, then the detail. Cover: what we build, which demo items it satisfies and how, the numbers we expect and where they come from, the build order with times, the demo script, and the limitations we will state. Questions for the team go at the end.

## 3. Reviewing a plan

A review goes at the **end of the plan file** as its own section, so the author's text stays untouched and readers see the plan first.

- Heading: `## Review: <who>, <date>`. First paragraph: who reviewed (a teammate by name, or the model, run by whom), what was read (the plan, which organiser files, which code), and that nothing in the section is a team decision.
- Second paragraph: **Verdict** in one sentence: GO, RESHAPE or KILL, and why.
- Then one short paragraph per finding, at most five, each with a bold lead of two or three words and at most four sentences: what is wrong, why it matters, the fix.
- Then, if the plan offers options, one paragraph on which option survives.
- Last line: `Not checked:` with what the review could not test.
- Plain words. Explain a term the first time it appears. No em-dash. Short comments on a single line still use `> note (name):` inline in the text.

## 4. How an agent operates here

- Facts and judgement are separate jobs. One worker checks every number, quote, file name and task id against the organiser files and the toolkit code; a different reviewer judges feasibility, scoring, fit to the brief and risk. The author of a text never reviews it.
- The reviewer is named in the file (for example "Review: Fable, 2026-11-06" means Claude Fable 5.1, run by whoever ran it). A reader must be able to tell a model's verdict from a teammate's.
- A review never edits the author's text. It appends. Corrections to facts in the author's text are findings in the review, not silent edits.
- Changes land as a branch and a pull request, never direct to main. The PR body says what was checked and what was not.
- Before anything is sent for a merge, read the result as a non-technical teammate would. If the first screen needs the data pack to make sense, add the plain-words part first.
- The team decides. Agents propose, compare, recommend and review. A row in `../decisions.md` is the only thing that makes a pick real.
